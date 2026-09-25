# blast test vector

`test.pk` and `test.txt` are copied unchanged from zlib `contrib/blast/test/`
(https://github.com/madler/zlib/tree/develop/contrib/blast). `test.pk` is a
PKWare DCL imploded stream that decompresses to `test.txt`. The DBC decoders
in `src/omnisus/sources/datasus_ftp/dbc.py` and
`native/omnisus-dbf/src/dbc.rs` are altered ports of `blast.c`, distributed
under this notice:

    Copyright (C) 2003, 2012, 2013 Mark Adler

    This software is provided 'as-is', without any express or implied
    warranty.  In no event will the author be held liable for any damages
    arising from the use of this software.

    Permission is granted to anyone to use this software for any purpose,
    including commercial applications, and to alter it and redistribute it
    freely, subject to the following restrictions:

    1. The origin of this software must not be misrepresented; you must not
       claim that you wrote the original software. If you use this software
       in a product, an acknowledgment in the product documentation would be
       appreciated but is not required.
    2. Altered source versions must be plainly marked as such, and must not be
       misrepresented as being the original software.
    3. This notice may not be removed or altered from any source distribution.
