import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import cv2
import numpy as np
from pathlib import Path
from typing import List
from app.config import settings

class OCRService:
    def __init__(self):
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert PIL Image to OpenCV format
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Apply thresholding to get better contrast
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Noise removal
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        processed = cv2.medianBlur(processed, 3)
        
        # Convert back to PIL Image
        return Image.fromarray(processed)
    
    def extract_text_from_image(self, image_path: Path) -> str:
        """Extract text from a single image"""
        try:
            image = Image.open(image_path)
            processed_image = self.preprocess_image(image)
            
            # Use Tesseract to extract text
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from image: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF by converting to images"""
        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, dpi=300)
            
            all_text = []
            for i, image in enumerate(images):
                # Preprocess and extract text from each page
                processed_image = self.preprocess_image(image)
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(processed_image, config=custom_config)
                all_text.append(f"--- Page {i+1} ---\n{text}")
            
            return "\n\n".join(all_text)
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from file (auto-detect type)"""
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")