from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anyio
import shutil
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
import tempfile
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="AetheroOS PDF Generator")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ReportRequest(BaseModel):
    office: str
    ref_code: str
    purpose: str
    findings: str
    recommendations: str
    author: str

# Custom styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='Center',
    parent=styles['Heading1'],
    alignment=1,  # Center alignment
    spaceAfter=30
))
styles.add(ParagraphStyle(
    name='Section',
    parent=styles['Heading2'],
    spaceBefore=20,
    spaceAfter=20
))

@app.post("/generate-pdf/")
async def generate_pdf(request: ReportRequest):
    # Create a temporary directory that will persist
    temp_dir = tempfile.mkdtemp()
    try:
        # Extract values from request
        office = request.office
        ref_code = request.ref_code
        purpose = request.purpose
        findings = request.findings
        recommendations = request.recommendations
        author = request.author

        pdf_path = os.path.join(temp_dir, f'ministerial_report_{ref_code}.pdf')
        logger.debug(f"Created temporary directory at {temp_dir}")
        logger.debug(f"PDF will be saved at {pdf_path}")

        # Create the PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        logger.debug(f"Created PDF document template at {pdf_path}")

        # Build the document content
        story = []

        # Header
        story.append(Paragraph("AETHEROOS MINISTERIAL REPORT", styles['Center']))
        story.append(Paragraph(f"Office of {office}", styles['Center']))
        story.append(Paragraph(f"Ref. Code: {ref_code}", styles['Center']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
        story.append(Spacer(1, 12))

        # Sections
        story.append(Paragraph("🪶 PURPOSE", styles['Section']))
        story.append(Paragraph(purpose, styles['Normal']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))

        story.append(Paragraph("🪶 FINDINGS", styles['Section']))
        story.append(Paragraph(findings, styles['Normal']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))

        story.append(Paragraph("🪶 RECOMMENDATIONS", styles['Section']))
        story.append(Paragraph(recommendations, styles['Normal']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))

        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Ministerial Seal: [ ⚜️ ]", styles['Center']))
        story.append(Paragraph(f"Signed: {author}", styles['Center']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Center']))

        # Build the PDF
        doc.build(story)
        logger.debug("PDF built successfully")

        # Verify the file exists and is readable
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not created at {pdf_path}")
            raise HTTPException(status_code=500, detail="Failed to create PDF file")

        try:
            with open(pdf_path, 'rb') as test_read:
                test_read.read(1)
            logger.debug("PDF file exists and is readable")
        except Exception as e:
            logger.error(f"Error verifying PDF file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to verify PDF file: {str(e)}")


        # Return the PDF file
        async def cleanup_temp_dir():
            await anyio.to_thread.run_sync(lambda: shutil.rmtree(temp_dir))

        response = FileResponse(
            pdf_path,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="ministerial_report_{ref_code}.pdf"'
            },
            background=cleanup_temp_dir
        )
        logger.debug("Created FileResponse successfully")
        return response

    except Exception as e:
        # Clean up on error
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
