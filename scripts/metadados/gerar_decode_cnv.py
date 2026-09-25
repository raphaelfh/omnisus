"""Escreve o `x-decode` dos campos que uma tabela CNV do TabWin decodifica.

Um campo ligado a um DBF relacionado (a segunda forma de linha do DEF, TabWin.pdf p. 88)
é escrito do mesmo jeito, com `method: dbf-parse`: a chave é o campo de mesmo nome do DBF
ou, sem ele, o primeiro campo; o rótulo é a coluna que o DEF nomeia. `largura`, se o
dataset a declara para o campo, guarda só os códigos com esse número de caracteres.

Entrada: `src/omnisus/data/dicionarios/sources/cnv/vinculos.json`, que nomeia, por
dataset, o DEF e o CNV de cada campo, e os membros empacotados com o SHA-256 lido do
arquivo oficial. Para cada campo o script confere o hash do membro, confere que o DEF
liga o campo àquele CNV na posição 1, escreve o mapa do CNV e uma claim
`/field/codes` com `method: cnv-parse`. Um mapa anterior sem claim de códigos que
discorda vira claim `conflicting` e um issue com o rótulo anterior de cada código. Uma
claim de códigos existente nunca é substituída: de outro método, ou `cnv-parse` com mapa
diferente, o script para e pede revisão. Uma linha de DEF fora
do layout só é ignorada se `linhas_fora_do_layout` a lista com o texto exato. Rodar de novo não muda
nada; `--check` falha se algum dicionário mudaria.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from omnisus.metadata import canonical_json, resolved_codes, sources_registry
from omnisus.transforms.cnv import (
    CnvFormatError,
    cnv_map,
    dbf_lookup_map,
    parse_cnv,
    parse_def,
    parse_def_lookups,
)

ROOT = Path(__file__).resolve().parents[2]
DICIONARIOS = ROOT / "src/omnisus/data/dicionarios"
CNV = DICIONARIOS / "sources/cnv"
METHOD = "cnv-parse"
DBF_METHOD = "dbf-parse"
REVIEWER = "scripts/metadados/gerar_decode_cnv.py"
ISSUE = "cnv-difere-do-mapa-anterior"


class _Dumper(yaml.SafeDumper):
    """Writes codes such as ``09`` and ``""`` quoted, so no YAML reader turns them into numbers."""


def _str(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    style = "'" if value == "" or value.isdigit() else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _str)


def read_member(path: str, membros: dict[str, Any]) -> str:
    raw = (CNV / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != membros[path]["sha256"]:
        raise ValueError(f"{path}: bytes differ from the archived member")
    if any(0x80 <= byte <= 0x9F for byte in raw):
        raise CnvFormatError(f"{path}: C1 byte; not latin-1 text")
    return raw.decode("latin-1")


def read_dbf_labels(
    path: str, membros: dict[str, Any], field: str, column: str, width: int | None
) -> dict[str, str]:
    """Code -> label from a related DBF member, whose bytes must be the archived ones.

    `width`, from `largura` in vinculos.json, keeps only codes of that many characters:
    MOTERRO.dbf holds a 4-character series whose text is CP850, and ER publishes only
    the 6-character one.
    """
    raw = (CNV / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != membros[path]["sha256"]:
        raise ValueError(f"{path}: bytes differ from the archived member")
    labels = dbf_lookup_map(raw, field.upper(), column)
    if width is not None:
        labels = {code: label for code, label in labels.items() if len(code) == width}
    if any(0x80 <= ord(c) <= 0x9F for text in labels.items() for part in text for c in part):
        raise CnvFormatError(f"{path}: C1 character; not latin-1 text")
    return labels


def read_def(path: str, vinculos: dict[str, Any]) -> str:
    """The DEF member's text with each reviewed `linhas_fora_do_layout` line blanked.

    Only a listed line is dropped, and only if its text matches exactly; a mismatch
    raises. Blanking (not deleting) keeps the line numbers of `parse_def` errors.
    """
    lines = read_member(path, vinculos["membros"]).splitlines(keepends=True)
    for entry in vinculos.get("linhas_fora_do_layout", []):
        if entry["membro"] != path:
            continue
        n = entry["linha"]
        found = lines[n - 1].rstrip("\r\n") if 0 < n <= len(lines) else None
        if found != entry["texto"]:
            raise ValueError(f"{path} line {n} is {found!r}, not {entry['texto']!r}")
        lines[n - 1] = lines[n - 1][len(found) :]
    return "".join(lines)


def binding_for(def_path: str, text: str, field: str, member: str) -> str:
    """The DEF line that binds `field` at position 1 to `member`, as a locator.

    A binding with an unknown start column (``start=None``, a field name where the
    column goes; TabWin.pdf pp. 87-88 documents no such form) is refused by name:
    such a field belongs in `sem_cnv`, never in `campos`.
    """
    folder = Path(def_path).parent
    unknown = False
    for b in parse_def(text):
        target = (folder / b.table.replace("\\", "/")).as_posix()
        if b.field != field.upper() or target.lower() != member.lower():
            continue
        if b.start == 1:
            return f"{Path(def_path).name}: {b.kind}{b.label}, {b.field}, {b.start}, {b.table}"
        unknown = unknown or b.start is None
    if unknown:
        raise ValueError(f"{def_path} binds {field} to {member} with an unknown start column")
    raise ValueError(f"{def_path} does not bind {field} to {member} at position 1")


def lookup_for(def_path: str, text: str, field: str, member: str) -> tuple[str, str]:
    """The DEF line relating `field` to the DBF `member` (p. 88), as a locator, and the
    column that holds the description."""
    folder = Path(def_path).parent
    for b in parse_def_lookups(text):
        target = (folder / b.table.replace("\\", "/")).as_posix()
        if b.field == field.upper() and target.lower() == member.lower():
            locator = f"{Path(def_path).name}: {b.kind}{b.label}, {b.field}, {b.column}, {b.table}"
            return locator, b.column
    raise ValueError(f"{def_path} does not relate {field} to {member}")


def regenerate(
    dataset: str,
    definition: dict[str, Any],
    decode: dict[str, str],
    evidence: dict[str, Any],
    checked_at: str,
    method: str = METHOD,
) -> dict[str, Any]:
    """The field with the table's map, or the field itself if its map of `method` is current.

    Only a field with no `/field/codes` claim is written. An existing claim of another
    method, or a claim of `method` whose map differs from `decode`, raises for review.
    """
    where = f"{dataset}.{definition['name']}"
    meta = definition.get("x-metadata", {})
    claims = list(meta.get("claims", []))
    current = next((c for c in claims if c["target"] == "/field/codes"), None)
    previous = {str(k): str(v) for k, v in definition.get("x-decode", {}).items()}
    if current is not None:
        if current["method"] != method:
            raise ValueError(
                f"{where}: /field/codes claim has method {current['method']!r} "
                f"(evidence {current.get('evidence')!r}); review it by hand before "
                "the table's map may replace it"
            )
        changed = sorted(
            c for c in previous.keys() | decode.keys() if previous.get(c) != decode.get(c)
        )
        if changed:
            raise ValueError(
                f"{where}: the table's map differs from the {method} map in codes {changed}; "
                "review the republished table and update the field by hand"
            )
        return definition
    digest = hashlib.sha256(
        canonical_json(resolved_codes({**definition, "x-decode": decode}))
    ).hexdigest()
    disagree = {code: label for code, label in previous.items() if decode.get(code) != label}
    table = "CNV" if method == METHOD else "DBF relacionado"
    claims.append(
        {
            "target": "/field/codes",
            "value_sha256": digest,
            "status": "conflicting" if disagree else "verified_in_source",
            "checked_at": checked_at,
            "method": method,
            "reviewer": REVIEWER,
            "evidence": [evidence],
            "note": f"Mapa do {table}; o mapa anterior está no issue {ISSUE}."
            if disagree
            else f"Mapa do {table}.",
        }
    )
    issues = list(meta.get("issues", []))
    if disagree:
        issues.append(
            {
                "id": ISSUE,
                "status": "open",
                "description": "Mapa anterior sem fonte substituído pelo CNV: "
                + "; ".join(
                    f"{code!r} era {label!r}, CNV "
                    + (repr(decode[code]) if code in decode else "não lista")
                    for code, label in disagree.items()
                ),
            }
        )
    new_meta = {**meta, "claims": claims}
    if issues:
        new_meta["issues"] = issues
    return {**definition, "x-decode": decode, "x-metadata": new_meta}


def replace_field(text: str, name: str, definition: dict[str, Any]) -> str:
    """Swap the one `- name: <name>` entry of the fields list for `definition`.

    The entry keeps its indentation: `    - name:` in most dictionaries, `  - name:`
    in the SINAN ones. A name found twice, or not at all, raises.
    """
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.lstrip(" ") == f"- name: {name}\n"]
    if len(starts) != 1:
        raise ValueError(f"{name}: {len(starts)} field entries with this name")
    start = starts[0]
    indent = lines[start][: len(lines[start]) - len(lines[start].lstrip(" "))]
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or lines[end].startswith(indent + "  ")):
        end += 1
    while not lines[end - 1].strip():
        end -= 1
    dumped = yaml.dump(
        [definition], Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100
    )
    block = "".join(indent + line if line.strip() else line for line in dumped.splitlines(True))
    return "".join(lines[:start]) + block + "".join(lines[end:])


def generate() -> dict[Path, str]:
    """New text of every dictionary the bindings touch."""
    vinculos = json.loads((CNV / "vinculos.json").read_text(encoding="utf-8"))
    membros = vinculos["membros"]
    registry = {s["id"]: s for s in sources_registry()["sources"]}
    out = {}
    for dataset, spec in vinculos["datasets"].items():
        path = DICIONARIOS / f"{dataset}.yaml"
        text = path.read_text(encoding="utf-8")
        fields = {f["name"]: f for f in yaml.safe_load(text)["schema"]["fields"]}
        def_text = read_def(spec["def"], vinculos)
        for field, member in spec["campos"].items():
            source = registry[membros[member]["fonte"]]
            if member.lower().endswith(".dbf"):
                line, column = lookup_for(spec["def"], def_text, field, member)
                width = spec.get("largura", {}).get(field)
                labels = read_dbf_labels(member, membros, field, column, width)
                method = DBF_METHOD
            else:
                line = binding_for(spec["def"], def_text, field, member)
                labels = cnv_map(parse_cnv(read_member(member, membros)))
                method = METHOD
            decode = dict(sorted(labels.items()))
            evidence = {
                "source_id": source["id"],
                "pages": [],
                "locator": f"{line}; {membros[member]['membro']}",
            }
            new = regenerate(
                dataset, fields[field], decode, evidence, source["retrieved_on"], method
            )
            if new is not fields[field]:
                text = replace_field(text, field, new)
        out[path] = text
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="falha se algo mudaria")
    args = parser.parse_args()
    generated = generate()
    changed = [p for p, t in generated.items() if p.read_text(encoding="utf-8") != t]
    if args.check:
        for p in changed:
            print(f"desatualizado: {p.relative_to(ROOT)}")
        return 1 if changed else 0
    for p in changed:
        p.write_text(generated[p], encoding="utf-8")
    print(f"{len(changed)} dicionários atualizados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
