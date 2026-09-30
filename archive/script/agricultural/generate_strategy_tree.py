import os
import sys
import traceback
from PIL import Image, ImageDraw, ImageFont

try:
    print("Trace: Initializing Pillow strategy tree script...", flush=True)
    
    # Ensure output directory exists
    out_dir = r"C:\Users\FlawiyaShirishMore\OneDrive - Africa Specialty Risks Ltd\ASR-Parametric_Research_Study\Africa-Flood-Study\output\agricultural\visualizations"
    os.makedirs(out_dir, exist_ok=True)

    # Create a blank image with a light slate grey background (slate-50: #f8fafc)
    img = Image.new('RGB', (1600, 1100), color='#f8fafc')
    draw = ImageDraw.Draw(img)

    # Helper function to draw rounded boxes
    def draw_box(draw, x1, y1, x2, y2, title, lines, fill_color, border_color, text_color='#ffffff', title_color='#ffffff'):
        # Draw rounded rectangle
        draw.rounded_rectangle([x1, y1, x2, y2], radius=15, fill=fill_color, outline=border_color, width=3)
        
        # Load Segoe UI standard font if available, fallback to default font
        try:
            title_font = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 22)
            body_font = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 15)
        except Exception:
            try:
                title_font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 22)
                body_font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 15)
            except Exception:
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
        
        # Draw title text centered
        w = x2 - x1
        draw.text((x1 + w/2, y1 + 30), title, fill=title_color, font=title_font, anchor='mm')
        
        # Draw body lines left-aligned with a margin
        for i, line in enumerate(lines):
            draw.text((x1 + 30, y1 + 65 + i*28), line, fill=text_color, font=body_font)

    # ── DRAW CONNECTIONS ──
    # Root bottom center: (800, 180) to branches
    draw.line([(800, 180), (800, 240)], fill='#94a3b8', width=4)
    draw.line([(340, 240), (1260, 240)], fill='#94a3b8', width=4)
    draw.line([(340, 240), (340, 300)], fill='#94a3b8', width=4)
    draw.line([(1260, 240), (1260, 300)], fill='#94a3b8', width=4)

    # Surface Flood bottom center: (1260, 600) to sub-branches
    draw.line([(1260, 600), (1260, 660)], fill='#94a3b8', width=4)
    draw.line([(1105, 660), (1395, 660)], fill='#94a3b8', width=4)
    draw.line([(1105, 660), (1105, 720)], fill='#94a3b8', width=4)
    draw.line([(1395, 660), (1395, 720)], fill='#94a3b8', width=4)

    # ── DRAW BOXES ──
    # 1. Root Box
    draw_box(draw, 600, 40, 1000, 180, 
             "Zambia Maize Crop Cycle", 
             ["• November to April", "• Parametric Policy Period"],
             fill_color='#1d4ed8', border_color='#3b82f6', text_color='#cbd5e1')

    # 2. Waterlogging Box
    draw_box(draw, 100, 300, 580, 600, 
             "Waterlogging Contract (Full Cycle)", 
             [
                 "• Damage Mechanism: Root Suffocation (Anoxia)",
                 "• Proxy Variable: Root-Zone Soil Moisture SSI (0-100cm)",
                 "• Standard Severe Threshold: SSI >= 1.50",
                 "• Trigger Criteria: SSI >= 1.20",
                 "• Duration Condition: >= 7 consecutive days",
                 "• Underwriting Payout: gradual yield reduction"
             ],
             fill_color='#065f46', border_color='#10b981', text_color='#a7f3d0')

    # 3. Surface Flood Box
    draw_box(draw, 1020, 300, 1500, 600, 
             "Surface Flood Contract", 
             [
                 "• Damage Mechanism: Canopy Submersion / Washout",
                 "• Proxy Variable: SCS CN Runoff Depth (Q) / Daily Rain",
                 "• Underwriting Intent: Protects against sudden floods",
                 "• Split Regime: Early Stage vs. Late Stage",
                 "• Custom CN Parameters: cultivated cropland CN=85",
                 "• Payout Basis: catastrophic physical stalk damage"
             ],
             fill_color='#7c2d12', border_color='#ea580c', text_color='#ffedd5')

    # 4. Early Stage Sub-box (Left under Surface Flood)
    draw_box(draw, 980, 720, 1230, 980, 
             "Early Stage (Nov - Dec)", 
             [
                 "• Crop Phase: Seedling Emerg.",
                 "• Threat: Seedling Drowning",
                 "• Criteria: Moderate Runoff",
                 "  (Q >= 10.0 mm or",
                 "   Daily Rain > Mean + 2σ)",
                 "• Payout: Replanting costs"
             ],
             fill_color='#fff5f5', border_color='#ef4444', text_color='#991b1b', title_color='#991b1b')

    # 5. Late Stage Sub-box (Right under Surface Flood)
    draw_box(draw, 1270, 720, 1520, 980, 
             "Late Stage (Jan - Apr)", 
             [
                 "• Crop Phase: Growth/Flowering",
                 "• Threat: stalk lodging/washout",
                 "• Criteria: Severe Runoff",
                 "  (Q >= 25.0 mm",
                 "   extreme storm events)",
                 "• Payout: Crop destruction"
             ],
             fill_color='#fff5f5', border_color='#ef4444', text_color='#991b1b', title_color='#991b1b')

    # Save image
    output_jpg_path = os.path.join(out_dir, "agricultural_flood_strategy_tree.jpg")
    img.save(output_jpg_path, "JPEG", quality=95)
    print(f"Trace: Strategy tree diagram saved successfully as JPEG to: {output_jpg_path}", flush=True)

except Exception as e:
    print(f"CRITICAL ERROR: {str(e)}", file=sys.stderr, flush=True)
    traceback.print_exc()
    sys.exit(1)
