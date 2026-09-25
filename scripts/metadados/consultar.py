"""Valida o contrato experimental e demonstra transporte, sem recodificar dados."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from omnisus import describe_dataset
from omnisus.metadata import canonical_json

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/dicionario"
SCHEMA = DOCS / "schemas/column-metadata.schema.json"


def resolve_pointer(document: dict, pointer: str) -> object:
    value = document
    for part in pointer.removeprefix("/").split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def validate_metadata(metadata: dict) -> None:
    """Valida estrutura e coerência; não substitui a checagem do documento."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(metadata)
    sources = {source["id"]: source for source in metadata["sources"]}
    if len(sources) != len(metadata["sources"]):
        raise ValueError("IDs de fontes duplicados")
    codes = [item["value"] for item in metadata["field"]["codes"]]
    if len(codes) != len(set(codes)):
        raise ValueError("Códigos duplicados")
    if metadata["field"]["id"] != f"{metadata['dataset']['id']}.{metadata['field']['name']}":
        raise ValueError("Identidade de campo incompatível com dataset/nome")
    targets = [claim["target"] for claim in metadata["claims"]]
    if len(targets) != len(set(targets)):
        raise ValueError("Afirmações duplicadas; reunir evidências e explicitar conflito")
    for claim in metadata["claims"]:
        digest = hashlib.sha256(
            canonical_json(resolve_pointer(metadata, claim["target"]))
        ).hexdigest()
        if digest != claim["value_sha256"]:
            raise ValueError(f"Valor alterado sem atualizar a revisão: {claim['target']}")
        for evidence in claim["evidence"]:
            if evidence["source_id"] not in sources:
                raise ValueError(f"Fonte não resolvida: {evidence['source_id']}")
            if (
                claim["status"] == "verified_in_source"
                and sources[evidence["source_id"]]["authority"] != "official"
            ):
                raise ValueError("Afirmação oficial verificada exige evidência primária")
    applicability = metadata["applicability"]
    for evidence in applicability["evidence"]:
        if evidence["source_id"] not in sources:
            raise ValueError(f"Fonte de aplicabilidade não resolvida: {evidence['source_id']}")
    if (
        applicability["valid_from"]
        and applicability["valid_until"]
        and applicability["valid_from"] >= applicability["valid_until"]
    ):
        raise ValueError("Intervalo de aplicabilidade vazio ou invertido")


def arrow_roundtrip(metadata: dict) -> None:
    """Usa representação textual vazia para transportar códigos sem convertê-los."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    payload = canonical_json(metadata)
    field = pa.field(metadata["field"]["name"], pa.string(), metadata={b"omnisus:column": payload})
    table = pa.Table.from_arrays([pa.array([], type=pa.string())], schema=pa.schema([field]))
    output = pa.BufferOutputStream()
    pq.write_table(table, output)
    restored = pq.read_table(pa.BufferReader(output.getvalue()))
    recovered = json.loads(restored.schema.field(field.name).metadata[b"omnisus:column"])
    if recovered != metadata or restored.num_rows != 0:
        raise ValueError("Metadados divergentes após Arrow → Parquet → Arrow")
    print("Arrow → Parquet → Arrow: metadados preservados; tabela vazia, sem conversão de dados.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    origin = parser.add_mutually_exclusive_group()
    origin.add_argument("--metadata", type=Path, help="Validate an archived example JSON.")
    origin.add_argument(
        "--dataset", default=None, help="Resolve a packaged dataset (default: sim_obitos)."
    )
    parser.add_argument("--field", default="sexo", help="Field to resolve (default: sexo).")
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument("--arrow", action="store_true")
    output_mode.add_argument(
        "--json", action="store_true", help="Emitir apenas o JSON validado no stdout, para pipes."
    )
    args = parser.parse_args()
    if args.metadata:
        metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    else:
        description = describe_dataset(args.dataset or "sim_obitos")
        matches = [
            item for item in description["fields"] if item["field"]["name"] == args.field.lower()
        ]
        if not matches:
            parser.error(f"Unknown field: {args.field}")
        metadata = matches[0]
    validate_metadata(metadata)
    if args.json:
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
        return
    print(
        f"Contrato válido: {metadata['field']['id']}; {len(metadata['field']['codes'])} códigos."
    )
    print(
        f"Aplicabilidade: {metadata['applicability']['status']} — {metadata['applicability']['reason']}"
    )
    if args.arrow:
        arrow_roundtrip(metadata)


if __name__ == "__main__":
    main()
