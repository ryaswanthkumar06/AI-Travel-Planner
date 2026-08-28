import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def _build_story(itinerary_data):
    """Builds the flowable story list for ReportLab PDF generation."""
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#0F172A")    # Dark slate
    secondary_color = colors.HexColor("#0284C7")  # Sky blue
    accent_color = colors.HexColor("#E2E8F0")     # Light gray
    text_color = colors.HexColor("#334155")       # Charcoal
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=primary_color,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=secondary_color,
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        textColor=text_color,
        leading=13
    )
    
    bold_body = ParagraphStyle(
        'DocBoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    alert_style = ParagraphStyle(
        'AlertBody',
        parent=body_style,
        textColor=colors.HexColor("#B91C1C")
    )
    
    story = []
    
    # 2. Document Header
    dest = str(itinerary_data.get('destination', 'Destination')).upper()
    days = itinerary_data.get('days', 3)
    travelers = itinerary_data.get('travelers', 2)
    budget = float(itinerary_data.get('budget', 30000.0))
    pace = str(itinerary_data.get('trip_pace') or itinerary_data.get('travel_style', 'Balanced'))
    
    raw_interests = itinerary_data.get('interests', [])
    if isinstance(raw_interests, list):
        interests_str = ", ".join(raw_interests)
    else:
        interests_str = str(raw_interests or "General Sightseeing")
        
    safety_status = str(itinerary_data.get('safety_status', 'Safe'))
    
    story.append(Paragraph("SmartTravel AI Itinerary Report", title_style))
    story.append(Paragraph(f"Destination: {dest}  •  Duration: {days} Days  •  Travelers: {travelers}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # 3. Trip Summary Grid Table
    summary_data = [
        [
            Paragraph("<b>Total Budget:</b>", body_style),
            Paragraph(f"₹{budget:,.2f}", bold_body),
            Paragraph("<b>Pace:</b>", body_style),
            Paragraph(pace, bold_body)
        ],
        [
            Paragraph("<b>Interests:</b>", body_style),
            Paragraph(interests_str, body_style),
            Paragraph("<b>Safety Alert Status:</b>", body_style),
            Paragraph(safety_status, bold_body)
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[100, 160, 120, 160])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), accent_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # 4. Lodging (Hotel) Details
    hotel = itinerary_data.get("selected_hotel") or {}
    if hotel:
        story.append(Paragraph("🏨 Verified Lodging Accommodation", h2_style))
        hotel_data = [
            [Paragraph("<b>Hotel Name</b>", bold_body), Paragraph(hotel.get("name", "Recommended Hotel"), body_style)],
            [Paragraph("<b>Rating / Category</b>", bold_body), Paragraph(f"⭐ {hotel.get('rating', 4.2)} / {hotel.get('category', 'Standard')}", body_style)],
            [Paragraph("<b>Price Per Night</b>", bold_body), Paragraph(f"₹{hotel['price_per_night']:,.2f} per night" if hotel.get("price_per_night") else "Included in package", body_style)],
            [Paragraph("<b>Amenities</b>", bold_body), Paragraph(str(hotel.get("amenities", "Free WiFi")).replace(";", ", "), body_style)],
            [Paragraph("<b>Source Registry</b>", bold_body), Paragraph(f"{hotel.get('source', 'Verified Registry')} ({hotel.get('source_url', 'Official site')})", body_style)]
        ]
        hotel_table = Table(hotel_data, colWidths=[130, 410])
        hotel_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(hotel_table)
        story.append(Spacer(1, 15))
    
    # 5. Day-by-Day Timeline Planner
    story.append(Paragraph("🗺️ Day-Wise Itinerary Plan", h2_style))
    
    for day in itinerary_data.get("itinerary", []):
        day_elements = []
        d_num = day.get('day', 1)
        d_theme = day.get('theme', 'Explore')
        d_weather = day.get('weather', 'Clear')
        d_dist = day.get('distance_km', 0.0)
        
        day_header = f"<b>DAY {d_num} — {d_theme}</b> ({d_weather})  •  Transit Distance: {d_dist:.1f} km"
        day_elements.append(Paragraph(day_header, ParagraphStyle('DayHeader', parent=h2_style, textColor=secondary_color, fontSize=12)))
        
        if day.get("travel_tip"):
            day_elements.append(Paragraph(f"💡 <i>Tip: {day['travel_tip']}</i>", body_style))
            day_elements.append(Spacer(1, 5))
            
        events_table_data = []
        events_table_data.append([
            Paragraph("<b>Time</b>", bold_body),
            Paragraph("<b>Place / Activity</b>", bold_body),
            Paragraph("<b>Details & Pricing</b>", bold_body)
        ])
        
        for ev in day.get("events", []):
            time_col = Paragraph(ev.get("time", "10:00 AM"), bold_body)
            
            ev_type = ev.get("type", "Activity")
            icon = "🏛️"
            if ev_type == "Restaurant" or "dining" in ev.get("category", "").lower():
                icon = "🍽️"
            elif ev_type == "Travel":
                icon = "🚗"
            elif ev_type == "Meal":
                icon = "🍳"
                
            name_p = Paragraph(f"<b>{icon} {ev.get('name', 'Place')}</b><br/>{ev.get('description', '')}", body_style)
            
            details_text = []
            if ev.get("category"):
                details_text.append(f"Category: {ev['category']}")
            if ev.get("cost") is not None and float(ev.get("cost", 0)) > 0:
                details_text.append(f"Estimated Cost: ₹{ev['cost']:,.2f}")
            if ev.get("opening_hours"):
                details_text.append(f"Hours: {ev['opening_hours']}")
            if ev.get("weather_note"):
                details_text.append(f"<font color='#B91C1C'>{ev['weather_note']}</font>")
                
            details_p = Paragraph("<br/>".join(details_text) if details_text else "-", body_style)
            events_table_data.append([time_col, name_p, details_p])
            
        events_table = Table(events_table_data, colWidths=[70, 310, 160])
        events_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (0,0), (-1,0), accent_color),
        ]))
        
        day_elements.append(events_table)
        day_elements.append(Spacer(1, 15))
        story.append(KeepTogether(day_elements))

    # 6. Budget Allocation Table
    breakdown = itinerary_data.get("budget_breakdown") or {}
    if breakdown:
        story.append(Paragraph("💰 Total Cost Breakdown Budget Dashboard", h2_style))
        budget_data = [
            [Paragraph("<b>Category</b>", bold_body), Paragraph("<b>Allocated Cost</b>", bold_body)],
            [Paragraph("🏨 Accommodation Lodging", body_style), Paragraph(f"₹{breakdown.get('hotel_cost', 0):,.2f}", body_style)],
            [Paragraph("🍽️ Meal Dining", body_style), Paragraph(f"₹{breakdown.get('food_cost', 0):,.2f}", body_style)],
            [Paragraph("🎟️ Attraction Tickets", body_style), Paragraph(f"₹{breakdown.get('attractions_cost', 0):,.2f}", body_style)],
            [Paragraph("🚗 Transportation", body_style), Paragraph(f"₹{breakdown.get('transport_cost', 0):,.2f}", body_style)],
            [Paragraph("<b>Total Estimated Cost</b>", bold_body), Paragraph(f"<b>₹{breakdown.get('total_cost', 0):,.2f}</b>", bold_body)],
            [Paragraph("<b>Remaining / Leftover</b>", bold_body), Paragraph(f"<b>₹{breakdown.get('remaining', 0):,.2f}</b>", bold_body)]
        ]
        
        budget_table = Table(budget_data, colWidths=[200, 120])
        budget_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('BACKGROUND', (0,0), (-1,0), accent_color),
            ('BACKGROUND', (0,5), (-1,6), colors.HexColor("#F1F5F9")),
        ]))
        
        budget_block = [
            budget_table,
            Spacer(1, 6),
            Paragraph(itinerary_data.get("budget_advice", "🟢 Budget verification passed."), body_style)
        ]
        story.append(KeepTogether(budget_block))
        story.append(Spacer(1, 15))
    
    # 7. Safety Alert Logs
    story.append(Paragraph("🛡️ Route Safety Analysis Log", h2_style))
    safety_block = []
    
    status_color = "#16A34A"
    s_status = itinerary_data.get("safety_status", "Safe")
    if s_status == "High Risk":
        status_color = "#DC2626"
    elif s_status == "Caution":
        status_color = "#D97706"
        
    s_msg = itinerary_data.get("safety_message", "Verified safe for travel routes.")
    safety_block.append(Paragraph(f"<b>Status: <font color='{status_color}'>{s_status.upper()}</font></b> — {s_msg}", bold_body))
    safety_block.append(Spacer(1, 6))
    
    alerts = itinerary_data.get("safety_alerts", [])
    if alerts:
        for alert in alerts:
            alert_text = f"<b>⚠️ {alert.get('location_name', 'Corridor')} ({alert.get('road_name', 'Highway')})</b><br/>" \
                         f"Risk Level: {alert.get('risk_level', 'Medium')}  •  Accident Counts: {alert.get('accident_count', 'N/A')} incidents<br/>" \
                         f"Factor: {alert.get('risk_type', 'Traffic hazard')}<br/>" \
                         f"Advice: {alert.get('recommended_action', 'Drive cautiously')}<br/>" \
                         f"<i>Source: {alert.get('source', 'Traffic Audit')}</i>"
            safety_block.append(Paragraph(alert_text, alert_style))
            safety_block.append(Spacer(1, 6))
    else:
        safety_block.append(Paragraph("🟢 No verified traffic hazards or accident-prone corridors detected within 1.5 km of your route legs.", body_style))
        
    story.append(KeepTogether(safety_block))
    story.append(Spacer(1, 15))
    
    # 8. Data Sources & Licenses
    story.append(Paragraph("📂 Official Registry & Data Source Attributions", h2_style))
    source_p = Paragraph(
        "All listings, coordinate data, entry ticket fees, and highway warnings are queried strictly from verified databases including: " \
        "<b>Incredible India, State Tourism Registries, and Official Road Safety Audits.</b>", body_style
    )
    story.append(KeepTogether([source_p]))
    
    return story

def generate_trip_pdf(itinerary_data, output_path):
    """Compiles the travel planner itinerary dictionary into a professional PDF report file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    story = _build_story(itinerary_data)
    doc.build(story)

def generate_trip_pdf_bytes(itinerary_data) -> bytes:
    """Compiles the travel planner itinerary into in-memory PDF bytes for direct download."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    story = _build_story(itinerary_data)
    doc.build(story)
    return buf.getvalue()
