import os
import time
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import pandas as pd
from io import StringIO
import glob
import ocrmypdf
# import pdftotext
import pdfplumber
import shutil
from pypdf import PdfReader

def is_pdf_tagged(pdf_path):
    reader = PdfReader(pdf_path)
    catalog = reader.trailer["/Root"]
    mark_info = catalog.get("/MarkInfo")
    if mark_info and mark_info.get("/Marked") == True:
        return True
    if "/StructTreeRoot" in catalog:
        return True
    return False

def pdf2img(pdf_path, output_dir=None, format = "JPEG"):
    """
    Convert the first page of a PDF to an image.

    Args:
        pdf_path (str): Path to the input PDF file.
        save_path (str, optional): Path to save the output image. If None, image is not saved.

    Returns:
        PIL.Image: The first page of the PDF as a PIL Image object.

    Raises:
        FileNotFoundError: If the PDF file does not exist.
        ValueError: If no pages are converted from the PDF.
        Exception: For other conversion errors.
    """
    try:
        # Verify PDF exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Convert PDF to images
        with open(pdf_path, "rb") as pdf_file:
            images = convert_from_bytes(pdf_file.read(), dpi = 300)

        # Check if images were generated
        if not images:
            raise ValueError("No pages converted from PDF")

        # Save the first page if save_path is provided
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        if output_dir is None:
            output_dir = f"{base_name}_img"
        os.makedirs(output_dir, exist_ok=True)

        for i, image in enumerate(images, 1):
            output_path = os.path.join(output_dir, f"{base_name}_{i}.jpg")
            image.save(output_path, format, quality=100)
            print(f"Saved page {i} to {output_path}")
        image_width, image_height = images[0].size
        print(f"Converted {len(images)} pages")

        return images, base_name

    except FileNotFoundError as e:
        raise e
    except IndexError:
        raise ValueError("No pages found in the PDF")
    except Exception as e:
        raise Exception(f"PDF conversion failed: {str(e)}")

def img2text(images, base_name, output_dir="text_output"):
    try:
        # Check if images list is empty
        if not images:
            raise ValueError("No images provided for text conversion")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Initialize text storage
        # Initialize text storage
        all_text = []

        config = r'--psm 11 -c preserve_interword_spaces=1'

        # Process each image
        # for i, image in enumerate(images, 1):
        #     # Extract data with positional information
        #     data = pytesseract.image_to_data(
        #         image,
        #         lang="eng+chi_sim+chi_tra",
        #         config="--psm 11",
        #         output_type=pytesseract.Output.STRING
        #     )
        #
        #     # Parse Tesseract output into a DataFrame
        #     df = pd.read_csv(StringIO(data), sep="\t", quoting=3)
        #
        #     # Filter for valid text entries (non-empty text at word level)
        #     df = df[df["level"] == 5]  # Level 5 corresponds to words
        #     df = df[df["text"].notna() & (df["text"].str.strip() != "")]
        #
        #     if df.empty:
        #         all_text.append(f"--- Page {i} ---\nNo text detected\n")
        #         print(f"No text detected on page {i}")
        #         continue
        #
        #     # Group by approximate rows based on 'top' coordinate
        #     # Use a threshold (e.g., 20 pixels) to group similar 'top' values into rows
        #     df["row_group"] = (df["top"] // 10).astype(int)
        #
        #     # Sort by row_group and left to maintain reading order
        #     df = df.sort_values(by=["row_group", "left"])
        #
        #     # Group by rows and format as table-like text
        #     rows = []
        #     for row_group, group in df.groupby("row_group"):
        #         # Sort by 'left' to approximate columns
        #         row_text = group.sort_values("left")["text"].str.strip().tolist()
        #         # Join with tabs to mimic columns
        #         rows.append("\t".join(row_text))
        #
        #     # Combine rows with newlines, add page header
        #     page_text = f"--- Page {i} ---\n" + "\n".join(rows) + "\n"
        #     all_text.append(page_text)
        #     print(f"Extracted text from page {i}")

        # Extract text from each image
        for i, image in enumerate(images, 1):
            text = pytesseract.image_to_string(
                image,
                lang = "chi_tra+chi_sim+eng",
                config=config)
            all_text.append(f"--- Page {i} ---\n{text}\n")
            print(f"Extracted text from page {i}\n")

        # Combine all text

        combined_text = "\n".join(all_text)

        # Save to text file
        output_path = os.path.join(output_dir, f"{base_name}.txt")
        with open(output_path, "w", encoding="utf-8") as text_file:
            text_file.write(combined_text)
        print(f"Saved text to {output_path}")

        return combined_text

    except ValueError as e:
        raise e
    except Exception as e:
        raise Exception(f"Text conversion failed: {str(e)}")

def process_pdfs_in_folder(input_dir= None, output_dir="text_output"):
    """
    Convert all PDFs in the input directory to text files, saving to the output directory.

    Args:
        input_dir (str): Directory containing PDF files. Defaults to 'sample_PDF'.
        output_dir (str): Directory to save text files. Defaults to 'text_output_rebuilt'.
    """
    try:
        # Verify input directory exists
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Get all PDF files in the input directory
        pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
        if not pdf_files:
            raise ValueError(f"No PDF files found in {input_dir}")

        # Process each PDF
        for pdf_path in pdf_files:
            try:
                # Get base name (filename without extension)
                base_name = os.path.splitext(os.path.basename(pdf_path))[0]

                # Convert PDF to text
                print(f"Processing {pdf_path}...")
                images, bname = pdf2img(pdf_path, output_dir="img_output")
                text = img2text(images, bname, output_dir)
                print(f"Completed {base_name}.txt")

            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
                continue

        print(f"Processed {len(pdf_files)} PDFs")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

def tagged_pdf(input_dir= None, output_dir="tagged_pdf", output_txt_dir="output_txt"):
    try:
        # Verify input directory exists
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(output_txt_dir, exist_ok=True)

        # Get all PDF files in the input directory
        pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
        if not pdf_files:
            raise ValueError(f"No PDF files found in {input_dir}")

        # Process each PDF
        for pdf_path in pdf_files:
            try:
                # Get base name (filename without extension)
                base_name = os.path.splitext(os.path.basename(pdf_path))[0]

                # Convert PDF to text
                print(f"Processing {pdf_path}...")
                output_pdf_path = os.path.join(output_dir, f"{base_name}_tagged.pdf")
                output_txt_path = os.path.join(output_txt_dir, f"{base_name}.txt")
                if not is_pdf_tagged(pdf_path):
                    ocrmypdf.ocr(pdf_path, output_pdf_path, lang="chi_tra+chi_sim+eng")
                else:
                    shutil.copy(pdf_path, output_pdf_path)

                with pdfplumber.open(output_pdf_path) as pdf:
                    all_text = []
                    combined_text = ""
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        all_text.append(text)
                combined_text = "\n".join(all_text)
                with open(output_txt_path, "w", encoding="utf-8") as text_file:
                    text_file.write(combined_text)
                print(f"Completed {base_name}.txt\n")

            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
                continue

        print(f"Processed {len(pdf_files)} PDFs")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":

    start_time = time.time()
    pdf_path = "sample_pdf"
    output_path = "text_output"
    # print(pytesseract.get_languages())
    # images, base_name = pdf2img(pdf_path, output_path)
    # combined_text = img2text(images, base_name)
    # input_pdf = "example3.pdf"
    # output_pdf = "example3_output.pdf"
    input_dir = "sample_pdf"
    process_pdfs_in_folder(input_dir, output_path)
    # tagged_pdf(input_dir)
    # with pdfplumber.open("example3_output.pdf") as pdf:
    #     text = pdf.pages[0].extract_text()
    #     print(text)
    print(f"Processed {pdf_path} in {round((time.time() - start_time),2)} seconds")