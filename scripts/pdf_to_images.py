import argparse
from pathlib import Path
import fitz  # PyMuPDF


def pdf_to_images(pdf_name: str, dpi: int = 200, image_format: str = "png"):

    pdf_file = f"{pdf_name}.pdf"

    basic_input_dir ="./source/pdfs"
    basic_output_dir = "./source/pages"

    pdf_path = Path(f"{basic_input_dir}/{pdf_file}")
    out_dir = Path(f"{basic_output_dir}/{pdf_name}")

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)

    # DPI를 확대 비율로 변환
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        output_path = out_dir / f"page_{page_index + 1:03d}.{image_format}"
        pix.save(output_path)

        print(f"Saved: {output_path}")

    print(f"\n완료: 총 {len(doc)}페이지 저장")
    doc.close()


def main():
    parser = argparse.ArgumentParser(description="PDF 페이지를 이미지로 변환합니다.")
    parser.add_argument("-p", "--pdf", help="입력 PDF 파일 경로")
    parser.add_argument("--dpi", type=int, default=200, help="이미지 DPI, 기본값 200")
    parser.add_argument("--format", default="png", choices=["png", "jpg", "jpeg"], help="이미지 포맷")

    args = parser.parse_args()

    pdf_to_images(
        pdf_name=args.pdf,
        dpi=args.dpi,
        image_format=args.format,
    )


if __name__ == "__main__":
    main()