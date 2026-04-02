"""PDF 페이지 추출 + 인쇄선 제거 웹앱.

실행: streamlit run app.py
"""

import io

import fitz  # PyMuPDF
import streamlit as st

st.set_page_config(page_title="PDF 페이지 추출기", page_icon="📄", layout="centered")
st.title("📄 PDF 페이지 추출기")
st.caption("원하는 페이지만 골라서 새 PDF로 만들어 줍니다. 인쇄선(재단선)은 자동으로 제거됩니다.")


def parse_pages(page_str: str, max_page: int) -> list[int]:
    """페이지 문자열을 파싱하여 0-based 인덱스 리스트로 반환."""
    pages = []
    for part in page_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            start, end = int(start), int(end)
            if start < 1 or end > max_page or start > end:
                raise ValueError(f"페이지 범위 {start}-{end}이 유효하지 않습니다 (전체: 1-{max_page})")
            pages.extend(range(start - 1, end))
        else:
            n = int(part)
            if n < 1 or n > max_page:
                raise ValueError(f"페이지 {n}이 유효하지 않습니다 (전체: 1-{max_page})")
            pages.append(n - 1)
    return pages


def extract_pdf(src_bytes: bytes, page_indices: list[int], remove_crop_marks: bool) -> bytes:
    """지정된 페이지를 추출하고 인쇄선을 제거한 PDF 바이트를 반환."""
    src = fitz.open(stream=src_bytes, filetype="pdf")
    doc = fitz.open()

    for idx in page_indices:
        doc.insert_pdf(src, from_page=idx, to_page=idx)

    if remove_crop_marks:
        for page in doc:
            trimbox = page.trimbox
            if trimbox != page.mediabox:
                page.set_cropbox(trimbox)

    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    doc.close()
    src.close()
    return buf.getvalue()


# --- 1단계: 파일 업로드 ---
uploaded = st.file_uploader("PDF 파일을 올려주세요", type=["pdf"])

if uploaded:
    src_bytes = uploaded.getvalue()
    src = fitz.open(stream=src_bytes, filetype="pdf")
    total = src.page_count

    # 인쇄선 존재 여부 자동 감지
    has_crop_marks = any(page.trimbox != page.mediabox for page in src)
    src.close()

    st.success(f"**{uploaded.name}** — 총 {total}페이지")

    # --- 2단계: 페이지 선택 ---
    st.subheader("추출할 페이지 선택")
    page_input = st.text_input(
        "페이지 번호 입력",
        placeholder="예: 1, 3, 5-10, 15-20",
        help="쉼표로 구분하고, 연속 페이지는 하이픈(-)으로 범위 지정",
    )

    # 인쇄선 제거 옵션 (인쇄선이 있을 때만 표시)
    remove_marks = False
    if has_crop_marks:
        remove_marks = st.checkbox("인쇄선(재단선) 제거", value=True)

    # --- 3단계: 추출 및 다운로드 ---
    if page_input:
        try:
            page_indices = parse_pages(page_input, total)
        except (ValueError, TypeError) as e:
            st.error(str(e))
            st.stop()

        if not page_indices:
            st.warning("추출할 페이지를 입력해 주세요.")
            st.stop()

        st.info(f"선택된 페이지: {len(page_indices)}개")

        result = extract_pdf(src_bytes, page_indices, remove_marks)

        output_name = uploaded.name.rsplit(".", 1)[0] + "_추출.pdf"
        st.download_button(
            label=f"📥 다운로드 ({len(page_indices)}페이지)",
            data=result,
            file_name=output_name,
            mime="application/pdf",
        )
