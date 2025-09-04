#!/usr/bin/env python3
"""Simple WeasyPrint test"""

def test_weasyprint_basic():
    try:
        from weasyprint import HTML, CSS
        
        # Simple test HTML
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial; padding: 20px; }
                h1 { color: #CDF95C; background: #004751; padding: 10px; }
            </style>
        </head>
        <body>
            <h1>WeasyPrint Test</h1>
            <p>This is a test of WeasyPrint PDF generation.</p>
        </body>
        </html>
        """
        
        # Generate PDF
        HTML(string=html_content).write_pdf('out/weasy_test.pdf')
        print("✅ WeasyPrint working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ WeasyPrint error: {e}")
        return False

if __name__ == '__main__':
    test_weasyprint_basic()