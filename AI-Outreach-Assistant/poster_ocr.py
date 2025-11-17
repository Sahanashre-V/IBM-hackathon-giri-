import pytesseract
import cv2

# Manually set the tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load your poster image
image = cv2.imread("input_posters/poster1.jpg")

# Convert image to text
text = pytesseract.image_to_string(image)

# Print the extracted text
print("\n🧠 Extracted Text from Poster:\n")
print(text)

# Optionally, save it to a text file
with open("extracted_text/poster1.txt", "w", encoding="utf-8") as f:
    f.write(text)