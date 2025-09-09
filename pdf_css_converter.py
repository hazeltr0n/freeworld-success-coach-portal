"""Convert CSS variables to hex colors for xhtml2pdf compatibility"""

def convert_css_variables_for_xhtml2pdf(html: str) -> str:
    """
    Convert CSS variables to actual hex colors since xhtml2pdf doesn't support them
    
    From your template's CSS variables:
    --fw-roots: #004751
    --fw-midnight: #191931  
    --fw-freedom-green: #CDF95C
    --fw-horizon-grey: #F4F4F4
    --fw-card-border: #CCCCCC
    --font-primary: 'Outfit', sans-serif (fallback to Arial for xhtml2pdf)
    """
    
    # FreeWorld brand color mapping
    css_var_replacements = {
        'var(--fw-roots)': '#004751',
        'var(--fw-midnight)': '#191931', 
        'var(--fw-freedom-green)': '#CDF95C',
        'var(--fw-horizon-grey)': '#F4F4F4',
        'var(--fw-card-border)': '#CCCCCC',
        'var(--fw-card-bg)': '#FAFAFA',
        'var(--font-primary)': 'Arial, sans-serif'  # xhtml2pdf works better with Arial
    }
    
    # Replace all CSS variables with actual values
    converted_html = html
    for css_var, replacement in css_var_replacements.items():
        converted_html = converted_html.replace(css_var, replacement)
    
    return converted_html