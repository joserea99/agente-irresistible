import jsPDF from 'jspdf';
import { Document, Packer, Paragraph, TextRun, HeadingLevel } from 'docx';
import { saveAs } from 'file-saver';

/**
 * Clean text for export by removing markdown-like artifacts if needed.
 * For now, we take raw text.
 */
const cleanText = (text: string) => text;

/**
 * Exports content to a PDF file.
 */
export const exportToPDF = (content: string, filename: string = 'irresistible-agent-response.pdf') => {
    const doc = new jsPDF();

    // Set font
    doc.setFont("helvetica");
    doc.setFontSize(12);

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 20;
    const maxLineWidth = pageWidth - (margin * 2);

    // Add Title
    doc.setFontSize(16);
    doc.setFont("helvetica", "bold");
    doc.text("Irresistible Agent Strategy", margin, 20);

    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.text(`Generated on: ${new Date().toLocaleDateString()}`, margin, 28);

    // Add Content
    doc.setFontSize(12);
    const splitText = doc.splitTextToSize(cleanText(content), maxLineWidth);

    let y = 40;

    splitText.forEach((line: string) => {
        if (y > pageHeight - margin) {
            doc.addPage();
            y = 20;
        }
        doc.text(line, margin, y);
        y += 7;
    });

    doc.save(filename);
};

/**
 * Exports content to a DOCX file.
 */
export const exportToDOCX = async (content: string, filename: string = 'irresistible-agent-response.docx') => {
    // Simple paragraph splitting by newlines for basic formatting
    const paragraphs = content.split('\n').map(line => {
        // Basic detection of headers (naive markdown parsing for #)
        if (line.startsWith('### ')) {
            return new Paragraph({
                text: line.replace('### ', ''),
                heading: HeadingLevel.HEADING_3,
                spacing: { before: 200, after: 100 }
            });
        }
        if (line.startsWith('## ')) {
            return new Paragraph({
                text: line.replace('## ', ''),
                heading: HeadingLevel.HEADING_2,
                spacing: { before: 200, after: 100 }
            });
        }
        if (line.startsWith('**') && line.endsWith('**')) {
            return new Paragraph({
                children: [new TextRun({ text: line.replace(/\*\*/g, ''), bold: true })],
                spacing: { before: 100, after: 100 }
            });
        }

        return new Paragraph({
            children: [new TextRun(line)],
            spacing: { after: 100 }
        });
    });

    const doc = new Document({
        sections: [
            {
                properties: {},
                children: [
                    new Paragraph({
                        text: "Irresistible Agent Strategy",
                        heading: HeadingLevel.TITLE,
                        spacing: { after: 300 }
                    }),
                    new Paragraph({
                        text: `Generated on: ${new Date().toLocaleDateString()}`,
                        spacing: { after: 500 }
                    }),
                    ...paragraphs,
                ],
            },
        ],
    });

    const blob = await Packer.toBlob(doc);
    saveAs(blob, filename);
};
