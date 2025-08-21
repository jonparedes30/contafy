from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    # Crear imagen con fondo verde CONTAFY
    img = Image.new('RGB', (size, size), '#27ae60')
    draw = ImageDraw.Draw(img)
    
    # Intentar cargar fuente, usar default si no está disponible
    try:
        font_size = size // 4
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Dibujar texto "C" centrado
    text = "C"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Guardar imagen
    img.save(output_path, 'PNG')
    print(f"Icono creado: {output_path}")

# Crear iconos en diferentes tamaños
sizes = [192, 512]
icons_dir = 'static/icons'

if not os.path.exists(icons_dir):
    os.makedirs(icons_dir)

for size in sizes:
    create_icon(size, f'{icons_dir}/icon-{size}x{size}.png')

print("Iconos PWA generados exitosamente!")