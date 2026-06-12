import html
import re
import zipfile
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "submission_project_documentation.md"
OUTPUT = ROOT / "docs" / "AI_Powered_Member_Portal_Chatbot_Project_Documentation.docx"


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def text_runs(text: str, font: str = "Arial", size: int = 22, bold: bool = False) -> str:
    parts = re.split(r"(`[^`]+`)", text)
    runs = []
    for part in parts:
        if not part:
            continue
        is_code = part.startswith("`") and part.endswith("`")
        clean = part[1:-1] if is_code else part
        run_font = "Consolas" if is_code else font
        run_size = 20 if is_code else size
        bold_xml = "<w:b/>" if bold else ""
        shade_xml = '<w:highlight w:val="lightGray"/>' if is_code else ""
        runs.append(
            "<w:r>"
            f"<w:rPr>{bold_xml}{shade_xml}<w:rFonts w:ascii=\"{run_font}\" w:hAnsi=\"{run_font}\"/>"
            f"<w:sz w:val=\"{run_size}\"/></w:rPr>"
            f"<w:t xml:space=\"preserve\">{esc(clean)}</w:t>"
            "</w:r>"
        )
    return "".join(runs)


def paragraph(text: str, style: str = "Normal", num_id: Optional[int] = None, ilvl: int = 0) -> str:
    style_sizes = {
        "ProjectTitle": 52,
        "Heading1": 40,
        "Heading2": 32,
        "Normal": 22,
    }
    style_bold = style in {"Heading1", "Heading2"}
    num_xml = ""
    if num_id is not None:
        num_xml = (
            "<w:numPr>"
            f"<w:ilvl w:val=\"{ilvl}\"/>"
            f"<w:numId w:val=\"{num_id}\"/>"
            "</w:numPr>"
        )
    return (
        "<w:p>"
        f"<w:pPr><w:pStyle w:val=\"{style}\"/>{num_xml}</w:pPr>"
        f"{text_runs(text, size=style_sizes.get(style, 22), bold=style_bold)}"
        "</w:p>"
    )


def code_paragraph(text: str) -> str:
    return (
        "<w:p>"
        "<w:pPr><w:pStyle w:val=\"CodeBlock\"/></w:pPr>"
        f"{text_runs(text, font='Consolas', size=20)}"
        "</w:p>"
    )


def table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    col_count = max(len(row) for row in rows)
    if col_count == 3:
        widths = [1800, 2300, 5260]
    else:
        widths = [9360 // col_count] * col_count
    grid = "".join(f"<w:gridCol w:w=\"{width}\"/>" for width in widths)
    table_rows = []
    for row_index, row in enumerate(rows):
        cells = []
        padded = row + [""] * (col_count - len(row))
        for col_index, cell in enumerate(padded):
            fill = "F8F9FA" if row_index == 0 else "FFFFFF"
            bold = row_index == 0
            cells.append(
                "<w:tc>"
                "<w:tcPr>"
                f"<w:tcW w:w=\"{widths[col_index]}\" w:type=\"dxa\"/>"
                f"<w:shd w:fill=\"{fill}\"/>"
                "<w:tcMar>"
                "<w:top w:w=\"80\" w:type=\"dxa\"/>"
                "<w:bottom w:w=\"80\" w:type=\"dxa\"/>"
                "<w:start w:w=\"120\" w:type=\"dxa\"/>"
                "<w:end w:w=\"120\" w:type=\"dxa\"/>"
                "</w:tcMar>"
                "</w:tcPr>"
                "<w:p><w:pPr><w:pStyle w:val=\"TableText\"/></w:pPr>"
                f"{text_runs(cell, size=20, bold=bold)}"
                "</w:p>"
                "</w:tc>"
            )
        table_rows.append("<w:tr>" + "".join(cells) + "</w:tr>")
    return (
        "<w:tbl>"
        "<w:tblPr>"
        "<w:tblW w:w=\"9360\" w:type=\"dxa\"/>"
        "<w:tblBorders>"
        "<w:top w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"DADCE0\"/>"
        "<w:left w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"DADCE0\"/>"
        "<w:bottom w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"DADCE0\"/>"
        "<w:right w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"DADCE0\"/>"
        "<w:insideH w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"DADCE0\"/>"
        "<w:insideV w:val=\"single\" w:sz=\"4\" w:space=\"0\" w:color=\"DADCE0\"/>"
        "</w:tblBorders>"
        "<w:tblLayout w:type=\"fixed\"/>"
        "</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>"
        + "".join(table_rows)
        + "</w:tbl>"
    )


def parse_markdown(markdown: str) -> list[str]:
    blocks = []
    lines = markdown.splitlines()
    i = 0
    in_code = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            i += 1
            continue
        if in_code:
            blocks.append(code_paragraph(line))
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                current = lines[i].strip()
                if not re.fullmatch(r"\|[\s:\-]+\|?", current.replace(" ", "")):
                    cells = [cell.strip() for cell in current.strip("|").split("|")]
                    if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                        table_lines.append(cells)
                i += 1
            blocks.append(table(table_lines))
            continue
        if stripped.startswith("# "):
            blocks.append(paragraph(stripped[2:], "ProjectTitle"))
        elif stripped.startswith("## "):
            blocks.append(paragraph(stripped[3:], "Heading1"))
        elif stripped.startswith("### "):
            blocks.append(paragraph(stripped[4:], "Heading2"))
        elif stripped.startswith("- "):
            blocks.append(paragraph(stripped[2:], "Normal", num_id=1))
        else:
            blocks.append(paragraph(stripped))
        i += 1
    return blocks


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:pPr><w:spacing w:after="160" w:line="276" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ProjectTitle">
    <w:name w:val="Project Title"/>
    <w:pPr><w:spacing w:after="60"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="52"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="Heading 1"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:keepNext/><w:spacing w:before="400" w:after="120"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="40"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="Heading 2"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:keepNext/><w:spacing w:before="320" w:after="80"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="CodeBlock">
    <w:name w:val="Code Block"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:after="80"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="20"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="TableText">
    <w:name w:val="Table Text"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="20"/></w:rPr>
  </w:style>
</w:styles>"""


def numbering_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="1">
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="bullet"/>
      <w:lvlText w:val="•"/>
      <w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:hint="default"/></w:rPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>
</w:numbering>"""


def document_xml(body_blocks: list[str]) -> str:
    body = "".join(body_blocks)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    {body}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""


def write_docx() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    blocks = parse_markdown(markdown)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>""",
        )
        docx.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""",
        )
        docx.writestr(
            "word/_rels/document.xml.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>""",
        )
        docx.writestr("word/document.xml", document_xml(blocks))
        docx.writestr("word/styles.xml", styles_xml())
        docx.writestr("word/numbering.xml", numbering_xml())


if __name__ == "__main__":
    write_docx()
    print(OUTPUT)
