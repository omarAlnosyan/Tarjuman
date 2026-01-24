# -*- coding: utf-8 -*-
"""
Process DOCX book and create chunks for RAG system - V2
Improved parsing for all poems including الحارث بن حلزة
"""

import sys
import json
import re
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

DOCX_PATH = "data/raw/شرح-المعلقات-السبع-للزوزني.docx"
OUTPUT_PATH = "data/processed/all_chunks_final.json"


def remove_diacritics(text):
    """Remove Arabic diacritics (tashkeel) for matching."""
    arabic_diacritics = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670]')
    return arabic_diacritics.sub('', text)


def extract_paragraphs(docx_path):
    """Extract all paragraphs from DOCX file."""
    print(f"Opening DOCX: {docx_path}")
    doc = Document(docx_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    print(f"Total paragraphs: {len(paragraphs)}")
    return paragraphs


def is_verse_number(text):
    """Check if text is a verse number like -1, -2, -3, etc."""
    return bool(re.match(r'^-\d+$', text.strip()))


def is_poem_header(text):
    """Check if text is a poem header."""
    normalized = remove_diacritics(text)
    
    # Check for poem headers
    poem_patterns = [
        'معلقة امرئ القيس',
        'معلقة امرؤ القيس',
        'معلقة طرفة',
        'معلقة زهير',
        'معلقة لبيد',
        'معلقة عمرو بن كلثوم',
        'معلقة عنترة',
        'معلقة الحارث',
    ]
    
    for pattern in poem_patterns:
        if pattern in normalized or pattern in text:
            return True
    
    # General pattern: starts with معلقة and is short
    if normalized.startswith('معلقة ') and len(normalized) < 50:
        return True
    
    return False


def get_poet_from_header(text):
    """Extract poet name from poem header."""
    normalized = remove_diacritics(text)
    
    poet_mapping = {
        'امرئ القيس': 'امرؤ القيس',
        'امرؤ القيس': 'امرؤ القيس',
        'طرفة': 'طرفة بن العبد',
        'زهير': 'زهير بن أبي سلمى',
        'لبيد': 'لبيد بن ربيعة',
        'عمرو بن كلثوم': 'عمرو بن كلثوم',
        'عنترة': 'عنترة بن شداد',
        'الحارث': 'الحارث بن حلزة',
    }
    
    for key, value in poet_mapping.items():
        if key in normalized or key in text:
            return value
    
    return None


def is_verse(text, next_text=None):
    """Check if text is likely a verse (not explanation)."""
    # Skip obvious non-verses
    if len(text) < 15 or len(text) > 250:
        return False
    if text.startswith('يقول:') or text.startswith('قيل:') or text.startswith('المراد'):
        return False
    if 'المصباح' in text or 'القاموس' in text:
        return False
    if text.startswith('شرح المعلقات'):
        return False
    if re.match(r'^\d+ \d+$', text):  # Page numbers
        return False
    if text == '(/)':
        return False
    
    # Check if it looks like prose explanation
    explanation_starters = ['الإيذان:', 'الإلحاح:', 'الغلو:', 'التكاليف:', 'الشناءة:']
    for starter in explanation_starters:
        if starter in text[:30]:
            return False
    
    # If next paragraph looks like explanation, this might be a verse
    if next_text:
        if next_text.startswith('يقول:') or next_text.startswith('قيل:'):
            return True
        if 'المراد' in next_text[:50] or 'المعنى' in next_text[:50]:
            return True
        if next_text.startswith('الإيذان:') or next_text.startswith('العهد:'):
            return True
    
    # Check for Arabic poetry patterns
    words = text.split()
    if len(words) >= 5:
        return True
    
    return False


def parse_poems(paragraphs):
    """Parse paragraphs to extract verses and explanations."""
    print("\nParsing poems...")
    
    # Initialize with all poets
    poems = {}
    for poet in ['امرؤ القيس', 'طرفة بن العبد', 'زهير بن أبي سلمى', 
                 'لبيد بن ربيعة', 'عمرو بن كلثوم', 'عنترة بن شداد', 
                 'الحارث بن حلزة']:
        poems[poet] = []
    
    current_poet = None
    current_verse = None
    current_explanation = []
    verse_number = 0
    
    i = 0
    while i < len(paragraphs):
        para = paragraphs[i]
        next_para = paragraphs[i + 1] if i + 1 < len(paragraphs) else ""
        
        # Check for poem header
        if is_poem_header(para):
            # Save previous verse
            if current_verse and current_poet and current_poet in poems:
                poems[current_poet].append({
                    'verse_text': current_verse,
                    'explanation': ' '.join(current_explanation),
                    'verse_number': verse_number
                })
            
            # Get poet from header
            poet = get_poet_from_header(para)
            if poet:
                current_poet = poet
                verse_number = 0
                current_verse = None
                current_explanation = []
                print(f"  Found poem: {para}")
                print(f"    -> Poet: {current_poet}")
            i += 1
            continue
        
        # Check for verse number
        if is_verse_number(para):
            # Save previous verse
            if current_verse and current_poet and current_poet in poems:
                poems[current_poet].append({
                    'verse_text': current_verse,
                    'explanation': ' '.join(current_explanation),
                    'verse_number': verse_number
                })
            
            verse_number = int(para.replace('-', ''))
            current_verse = None
            current_explanation = []
            i += 1
            continue
        
        # Check if this is a verse
        if current_poet and current_verse is None and is_verse(para, next_para):
            current_verse = para
            i += 1
            continue
        
        # Otherwise it's explanation
        if current_verse and len(para) > 15:
            # Skip page numbers and headers
            if not re.match(r'^\d+ \d+$', para) and para != '(/)' and not para.startswith('شرح المعلقات'):
                current_explanation.append(para)
        
        i += 1
    
    # Save last verse
    if current_verse and current_poet and current_poet in poems:
        poems[current_poet].append({
            'verse_text': current_verse,
            'explanation': ' '.join(current_explanation),
            'verse_number': verse_number
        })
    
    # Print stats
    print("\nResults:")
    total = 0
    for poet, verses in poems.items():
        print(f"  {poet}: {len(verses)} verses")
        total += len(verses)
    print(f"  TOTAL: {total} verses")
    
    return poems


def create_chunks(poems):
    """Create chunks for RAG system."""
    print("\nCreating chunks...")
    
    chunks = []
    chunk_id = 0
    
    for poet_name, verses in poems.items():
        poem_name = f"معلقة {poet_name}"
        
        for verse in verses:
            chunk_id += 1
            chunk = {
                'chunk_id': chunk_id,
                'chunk_type': 'verse_with_explanation',
                'chunk_index': 0,
                'text': f"البيت: {verse['verse_text']}\n\nالشرح: {verse['explanation']}",
                'verse_text': verse['verse_text'],
                'verse_number': verse['verse_number'],
                'poet_name': poet_name,
                'poem_name': poem_name,
                'source': {
                    'file': 'شرح-المعلقات-السبع-للزوزني.docx',
                    'book': 'شرح المعلقات السبع للزوزني'
                },
                'metadata': {
                    'char_count': len(verse['verse_text']) + len(verse['explanation']),
                    'has_explanation': len(verse['explanation']) > 20
                }
            }
            chunks.append(chunk)
    
    print(f"Created {len(chunks)} chunks")
    return chunks


def main():
    print("=" * 60)
    print("DOCX Processing V2 - Improved Parsing")
    print("=" * 60)
    
    # Step 1: Extract paragraphs
    paragraphs = extract_paragraphs(DOCX_PATH)
    
    # Step 2: Parse poems
    poems = parse_poems(paragraphs)
    
    # Step 3: Create chunks
    chunks = create_chunks(poems)
    
    # Step 4: Save chunks
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT_PATH}")
    
    # Show الحارث samples
    print("\n" + "=" * 60)
    print("Sample verses from الحارث بن حلزة:")
    print("=" * 60)
    harith_verses = [c for c in chunks if 'الحارث' in c['poet_name']]
    for chunk in harith_verses[:5]:
        print(f"\n[{chunk['chunk_id']}] بيت {chunk['verse_number']}")
        print(f"  {chunk['verse_text'][:80]}...")
    
    print(f"\nTotal الحارث verses: {len(harith_verses)}")
    print("\nDone!")


if __name__ == "__main__":
    main()
