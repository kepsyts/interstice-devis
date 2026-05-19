from flask import Flask, request, jsonify, send_file, render_template
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import io
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# ── Route principale — sert le formulaire ──
@app.route('/')
def index():
    return app.send_static_file('index.html')

# ── Route PDF ──
@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400

        # Calculs
        lignes = data.get('lignes', [])
        total_ht  = sum((l.get('qte', 1) or 1) * (l.get('pu', 0) or 0) for l in lignes)
        total_tva = total_ht * 0.2
        total_ttc = total_ht + total_tva

        # Dates
        date_str = data.get('date', '')
        date_fr = ''
        date_exp = ''
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            date_fr = dt.strftime('%d/%m/%Y')
            validite = int(data.get('validite', 30) or 30)
            dt_exp = dt + timedelta(days=validite)
            date_exp = dt_exp.strftime('%d/%m/%Y')
        except:
            pass

        # Émetteur (valeurs par défaut)
        emt = data.get('emetteur', {})
        if not emt:
            emt = {
                'nom': 'INTERSTICE PRODUCTIONS',
                'adresse': '151B Avenue Pierre Brossolette',
                'ville': '94170 Le Perreux-sur-Marne, FR',
                'email': 'contact@intersticeproductions.com',
                'siret': '990 305 427 00017',
                'tva': 'FR02990305427',
                'footer': 'INTERSTICE PRODUCTIONS, SARL au capital de 100,00 € · Creteil B 990305427'
            }

        # Conditions
        conds = data.get('conditions', {})
        if not conds.get('acompte'):
            conds['acompte'] = data.get('reglement', 'Acompte 50% à la commande, solde à la livraison des fichiers finaux.')
        if not conds.get('sauvegarde'):
            conds['sauvegarde'] = 'Les fichiers sont sauvegardés 3 mois maximum à compter de la date de livraison.'
        if not conds.get('droits'):
            conds['droits'] = "Le client autorise Interstice Productions à utiliser les contenus produits à des fins de communication et de promotion, sauf demande écrite contraire formulée avant la signature du devis."
        if not conds.get('assurance'):
            conds['assurance'] = "L'activité est couverte par une assurance Responsabilité Civile Professionnelle auprès d'ORUS."

        # Thème couleur
        theme = data.get('theme', 'rouge')
        if theme == 'noir':
            theme_primary      = '#111111'
            theme_primary_dark = '#000000'
            theme_on_primary   = '#ffffff'
            watermark_url      = 'https://static.wixstatic.com/media/02d2d0_579c0b2eaafd43818a6d51e8eadee53e~mv2.png'
        else:
            theme_primary      = '#cc0000'
            theme_primary_dark = '#990000'
            theme_on_primary   = '#ffffff'
            watermark_url      = 'https://static.wixstatic.com/media/02d2d0_3e7c25002e0d4cfc95e2ec69c8781a9d~mv2.png'

        # Contexte pour le template
        context = {
            'intitule': data.get('intitule', 'Devis'),
            'num': data.get('num', 'DEV-001'),
            'date_fr': date_fr,
            'date_exp': date_exp,
            'client': data.get('client', {}),
            'message': data.get('message', ''),
            'lignes': lignes,
            'total_ht': fmt(total_ht),
            'total_tva': fmt(total_tva),
            'total_ttc': fmt(total_ttc),
            'emt': emt,
            'conds': conds,
            'theme_primary': theme_primary,
            'theme_primary_dark': theme_primary_dark,
            'theme_on_primary': theme_on_primary,
            'watermark_url': watermark_url,
        }

        # Générer le HTML du devis
        html_content = render_template('devis.html', **context)

        # Convertir en PDF avec WeasyPrint
        font_config = FontConfiguration()
        html_obj = HTML(string=html_content, base_url='https://interstice-devis.onrender.com')
        css_fonts = CSS(
            string='@import url("https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap");',
            font_config=font_config
        )
        pdf_bytes = html_obj.write_pdf(stylesheets=[css_fonts], font_config=font_config)

        # Retourner le PDF
        filename = f"devis_{data.get('num', 'DEV-001')}_{(data.get('client', {}).get('nom', 'client') or 'client').replace(' ', '_')}.pdf"
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"Erreur PDF: {e}")
        return jsonify({'error': str(e)}), 500


def fmt(n):
    """Formater un nombre en prix français"""
    try:
        val = float(n or 0)
        return f"{val:,.2f}".replace(',', ' ').replace('.', ',') + ' €'
    except:
        return '0,00 €'


if __name__ == '__main__':
    app.run(debug=True, port=5000)
