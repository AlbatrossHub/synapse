import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

INPUT_FILE = '/opt/odoo18/custom_addons/synapse/dasii.txt'
OUTPUT_FILE = '/opt/odoo18/custom_addons/synapse/dasii_assessment/data/dasii_data.xml'

def clean_line(line):
    return line.strip()

def parse_dasii():
    with open(INPUT_FILE, 'r') as f:
        lines = f.readlines()

    clusters = []
    items = []
    
    current_scale = None
    
    # Regex for items: Number, Description, Ages, Cluster
    # Example: 105. Uncovers square box 11.4 9.8 14.4 III
    # But sometimes description is multi-line.
    # We will look for lines starting with a number followed by dot.
    
    item_pattern = re.compile(r'^(\d+)\.\s+(.*?)\s+(\d+\.?\d*)\s+(\d+\.?\d*[\*\-]?)\s+(\d+\.?\d*[\*\-\+]?)\s+([IVX]+)$')
    
    # Regex for Clusters table
    # Motor I Neck control ...
    
    # We'll do a two-pass or state machine approach.
    
    # 1. Parse Clusters from the end of the file manualy or via specific search
    # content is roughly at the end.
    
    cluster_start = False
    
    # Manual hardcoded clusters based on PDF analysis to ensure accuracy 
    # since text parsing table columns is flaky with spaces.
    
    # Motor Clusters
    cluster_data = [
        {'code': 'I', 'name': 'Neck control', 'scale': 'motor', 'sequence': 10},
        {'code': 'II', 'name': 'Body Control', 'scale': 'motor', 'sequence': 20},
        {'code': 'III', 'name': 'Locomotion I: Coordinated movements', 'scale': 'motor', 'sequence': 30},
        {'code': 'IV', 'name': 'Locomotion II: Skills', 'scale': 'motor', 'sequence': 40},
        {'code': 'V', 'name': 'Manipulation', 'scale': 'motor', 'sequence': 50},
        # Mental Clusters
        {'code': 'I', 'name': 'Cognizance - Visual', 'scale': 'mental', 'sequence': 10},
        {'code': 'II', 'name': 'Cognizance - Auditory', 'scale': 'mental', 'sequence': 20},
        {'code': 'III', 'name': 'Reaching, manipulation, and exploring', 'scale': 'mental', 'sequence': 30},
        {'code': 'IV', 'name': 'Memory', 'scale': 'mental', 'sequence': 40},
        {'code': 'V', 'name': 'Social interaction and imitative behavior', 'scale': 'mental', 'sequence': 50},
        {'code': 'VI', 'name': 'Language - Vocalization, speech, and comm.', 'scale': 'mental', 'sequence': 60},
        {'code': 'VII', 'name': 'Language - Vocabulary and comprehension', 'scale': 'mental', 'sequence': 70},
        {'code': 'VIII', 'name': 'Understanding relationship', 'scale': 'mental', 'sequence': 80},
        {'code': 'IX', 'name': 'Differentiation by use, shapes, and movements', 'scale': 'mental', 'sequence': 90},
        {'code': 'X', 'name': 'Manual dexterity', 'scale': 'mental', 'sequence': 100},
    ]
    
    # 2. Parse Items
    # We scan lines. If we see "Dash Motor Scale", set scale=motor etc.
    
    parsing_items = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        if "Dash Motor Scale" in line:
            current_scale = 'motor'
            parsing_items = True
            continue
        if "Dash Mental Scale" in line:
            current_scale = 'mental'
            parsing_items = True
            continue
        if "DASII Content Clusters" in line:
            parsing_items = False
            break
            
        if parsing_items:
            # Attempt to match item line
            # Handle page breaks/headers
            if "Item description" in line or "Item No." in line:
                continue
            
            # Basic parsing logic
            # Look for starting digits
            match =  re.match(r'^(\d+)\.\s+(.*)', line)
            if match:
                item_no = match.group(1)
                rest = match.group(2)
                
                # The rest contains description + metrics + cluster
                # We need to split by spacing or regex from the right
                # Valid ages are numbers like .1, 1.4, 20.3
                
                # Try to extract the metrics from the end of the line
                # Format: 50% 3% 97% Cluster
                # Ex: .1 .1* 1.4 I
                # Ex: 11.4 9.8 14.4 III
                
                metrics_match = re.search(r'(\.?\d+)\s+(\.?\d+[\*\-\+]?)\s+(\.?\d+[\*\-\+]?)\s+([IVX]+)$', rest)
                
                # Strategy 2: Split by whitespace
                # The last token should be Roman Numeral (Cluster)
                # The 3 tokens before that should be the ages.
                # Everything else is description.
                
                parts = rest.split()
                if len(parts) >= 4:
                    cluster_code = parts[-1]
                    age_97_str = parts[-2]
                    age_3_str = parts[-3]
                    age_50_str = parts[-4]
                    
                    # Validate if cluster is Roman Numeral-ish
                    if re.match(r'^[IVX]+$', cluster_code):
                         # Reconstruct description
                         # removing the last 4 parts from the original string might be safer to preserve internal spaces
                         # but for now joining the remaining parts is fine.
                         description = " ".join(parts[:-4])
                         
                         items.append({
                            'item_no': item_no,
                            'description': description,
                            'age_50': float( re.sub(r'[^\d.]', '', age_50_str) or 0 ),
                            'age_3': float( re.sub(r'[^\d.]', '', age_3_str) or 0 ),
                            'age_97': float( re.sub(r'[^\d.]', '', age_97_str) or 0 ),
                            'cluster_code': cluster_code,
                            'scale': current_scale
                        })
                    else:
                        print(f"Cluster validation failed: {line}")
                else:
                    print(f"Not enough parts: {line}")
    
    print(f"Found {len(items)} items")

    # Explicit Mapping provided by User
    # Maps (scale, item_no) -> cluster_code
    explicit_mapping = {}
    
    # Mental Mappings
    mental_map = {
        'I': [2, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 18, 22, 25, 31, 32, 33, 38, 40, 44, 47, 54, 60, 84, 90],
        'II': [1, 4, 5, 6, 23, 45, 46],
        'III': [34, 35, 36, 37, 41, 42, 43, 49, 50, 51, 53, 55, 56, 59, 63, 64, 66, 67, 68, 69, 70, 71, 72, 73, 75, 77, 79, 89, 98, 105, 108, 112, 113, 119, 142, 162],
        'IV': [26, 30, 39, 61, 62, 74, 83, 87, 91, 97, 129],
        'V': [3, 20, 21, 24, 27, 28, 48, 52, 58, 65, 76, 78, 95, 99, 100, 101, 103, 107, 109, 120, 149, 151],
        'VI': [15, 19, 29, 57, 82, 86, 94, 111, 114, 126, 140],
        'VII': [81, 88, 92, 93, 102, 106, 115, 124, 131, 135, 137, 141, 143, 147, 148, 157, 158, 161],
        'VIII': [80, 116, 117, 118, 122, 125, 127, 128, 132, 133, 138, 145, 146, 150, 153, 156, 160, 163],
        'IX': [85, 96, 104, 110, 130, 134, 139, 152],
        'X': [121, 123, 136, 144, 154, 155, 159]
    }
    for code, numbers in mental_map.items():
        for number in numbers:
            explicit_mapping[('mental', str(number))] = code

    # Motor Mappings
    motor_map = {
        'I': [1, 2, 7, 11, 13, 14, 19],
        'II': [4, 5, 6, 8, 9, 12, 15, 18, 20, 22, 23, 26, 27, 29, 30, 31, 37, 39, 44, 45, 46, 56, 67],
        'III': [3, 33, 34, 38, 42, 48, 49, 50, 53, 54],
        'IV': [51, 52, 55, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66],
        'V': [10, 16, 17, 21, 24, 25, 28, 32, 35, 36, 40, 41, 43, 47]
    }
    for code, numbers in motor_map.items():
        for number in numbers:
            explicit_mapping[('motor', str(number))] = code

    # Generate XML
    odoo = ET.Element('odoo')
    data = ET.SubElement(odoo, 'data', noupdate="0")
    
    # Create Clusters
    cluster_xml_ids = {} # (scale, code) -> xml_id
    
    for c in cluster_data:
        record_id = f"cluster_{c['scale']}_{c['code']}"
        cluster_xml_ids[(c['scale'], c['code'])] = record_id
        
        record = ET.SubElement(data, 'record', id=record_id, model='dasii.cluster')
        ET.SubElement(record, 'field', name='name').text = c['name']
        ET.SubElement(record, 'field', name='code').text = c['code']
        ET.SubElement(record, 'field', name='scale').text = c['scale']
        ET.SubElement(record, 'field', name='sequence').text = str(c['sequence'])

    # Create Items
    for item in items:
        # Override cluster from explicit mapping if exists
        key = (item['scale'], item['item_no'])
        if key in explicit_mapping:
            item['cluster_code'] = explicit_mapping[key]
        
        record_id = f"item_{item['scale']}_{item['item_no']}"
        record = ET.SubElement(data, 'record', id=record_id, model='dasii.item')
        
        ET.SubElement(record, 'field', name='item_no').text = item['item_no']
        ET.SubElement(record, 'field', name='description').text = item['description']
        ET.SubElement(record, 'field', name='scale').text = item['scale']
        ET.SubElement(record, 'field', name='age_50').text = str(item['age_50'])
        ET.SubElement(record, 'field', name='age_3').text = str(item['age_3'])
        ET.SubElement(record, 'field', name='age_97').text = str(item['age_97'])
        
        # Link to cluster
        c_xml_id = cluster_xml_ids.get((item['scale'], item['cluster_code']))
        if c_xml_id:
             ET.SubElement(record, 'field', name='cluster_id', ref=c_xml_id)
        else:
             print(f"Warning: Cluster not found for {key} -> {item['cluster_code']}")

    xmlstr = minidom.parseString(ET.tostring(odoo)).toprettyxml(indent="    ")
    with open(OUTPUT_FILE, "w") as f:
        f.write(xmlstr)

if __name__ == '__main__':
    parse_dasii()
