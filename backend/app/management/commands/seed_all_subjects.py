import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.department import Department
from app.models.course import Course
from app.models.subject import Subject

def get_base_topics(dept_code):
    topics = {
        "BT-CS": ["Programming", "Algorithms", "Data Structures", "Databases", "Networks", "Operating Systems", "AI", "Machine Learning", "Software Engineering", "Cybersecurity", "Cloud Computing", "Web Development", "Computer Architecture", "Theory of Computation", "Compiler Design"],
        "BT-ME": ["Mechanics", "Thermodynamics", "Fluids", "Manufacturing", "Machine Design", "Heat Transfer", "CAD", "Robotics", "Dynamics", "Material Science", "Mechatronics", "Automotive Engineering", "Vibrations", "Kinematics", "Energy Conversion"],
        "BT-CE": ["Surveying", "Materials", "Structural Analysis", "Geotechnical", "Fluid Mechanics", "Transportation", "Environmental", "Concrete Technology", "Steel Design", "Hydraulics", "Construction Management", "Town Planning", "Water Resources", "Estimation", "Bridge Engineering"],
        "BT-EE": ["Circuits", "Electromagnetics", "Electrical Machines", "Power Systems", "Control Systems", "Microprocessors", "Power Electronics", "Signals and Systems", "Instrumentation", "Renewable Energy", "High Voltage", "Switchgear", "Digital Electronics", "Network Analysis", "Electric Drives"],
        "BT-EC": ["Signals", "Digital Logic", "Analog Circuits", "Communications", "VLSI", "DSP", "Antennas", "Microcontrollers", "Embedded Systems", "Optical Communication", "Wireless Networks", "Radar Systems", "Microwave Engineering", "Information Theory", "CMOS Design"],
        "BT-AS": ["Physics", "Mathematics", "Chemistry", "English", "Environmental Science", "Engineering Drawing", "Basic Electrical", "Basic Mechanical", "Programming Fundamentals", "Workshop Practice"],
        "MT-AI": ["Deep Learning", "NLP", "Computer Vision", "Reinforcement Learning", "Optimization", "Advanced AI", "Neural Networks", "Robotics and AI", "Speech Processing", "Cognitive Computing"],
        "MT-DS": ["Data Mining", "Big Data", "Advanced Statistics", "Machine Learning Algorithms", "Data Visualization", "Predictive Modeling", "Cloud Data", "Hadoop Ecosystem", "Time Series Analysis", "Data Security"],
        "MT-STE": ["Advanced Structural Analysis", "Finite Element Method", "Earthquake Engineering", "Structural Dynamics", "Steel Structures", "Prestressed Concrete", "Bridge Design", "Plates and Shells", "Reliability", "Tall Buildings"],
        "MT-TE": ["Advanced Thermodynamics", "Heat Pipes", "Computational Fluid Dynamics", "Cryogenics", "Combustion", "Solar Thermal", "Convective Heat Transfer", "Gas Turbines", "Refrigeration", "Thermal Power"],
        "MT-VD": ["Advanced VLSI Design", "ASIC Design", "Mixed Signal IC", "System on Chip", "Nanoelectronics", "Testing and Verification", "Low Power VLSI", "RF IC Design", "Memory Design", "CAD for VLSI"],
        "BS-PHY": ["Mechanics", "Optics", "Electromagnetism", "Quantum Mechanics", "Solid State", "Nuclear Physics", "Thermodynamics", "Mathematical Physics", "Atomic Physics", "Electronics", "Relativity", "Statistical Mechanics", "Astrophysics", "Particle Physics", "Plasma Physics"],
        "BS-CHE": ["Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry", "Analytical Chemistry", "Biochemistry", "Spectroscopy", "Polymer Chemistry", "Environmental Chemistry", "Industrial Chemistry", "Nuclear Chemistry", "Green Chemistry", "Electrochemistry", "Quantum Chemistry", "Stereochemistry", "Medicinal Chemistry"],
        "BS-MAT": ["Calculus", "Algebra", "Real Analysis", "Topology", "Differential Equations", "Number Theory", "Complex Analysis", "Linear Algebra", "Geometry", "Probability", "Statistics", "Numerical Methods", "Optimization", "Discrete Mathematics", "Vector Calculus"],
        "BS-ZOO": ["Animal Diversity", "Physiology", "Genetics", "Evolution", "Ecology", "Immunology", "Cell Biology", "Developmental Biology", "Endocrinology", "Animal Behavior", "Zoogeography", "Parasitology", "Entomology", "Marine Biology", "Wildlife Conservation"],
        "BS-BOT": ["Plant Diversity", "Anatomy", "Plant Physiology", "Plant Genetics", "Pathology", "Biotechnology", "Taxonomy", "Ecology", "Economic Botany", "Microbiology", "Phycology", "Mycology", "Bryology", "Pteridology", "Gymnosperms"],
        "BA-ENG": ["British Literature", "American Literature", "Literary Theory", "Linguistics", "Poetry", "Drama", "Prose", "Postcolonial Literature", "World Literature", "Women's Writing", "Creative Writing", "Phonetics", "Indian English", "Translation Studies", "Cultural Studies"],
        "BA-HIS": ["Ancient History", "Medieval History", "Modern History", "World History", "Historiography", "European History", "American History", "Asian History", "History of Art", "Cultural History", "Economic History", "Military History", "Diplomatic History", "Social History", "Regional History"],
        "BA-POL": ["Political Theory", "Comparative Politics", "International Relations", "Public Administration", "Indian Constitution", "Western Political Thought", "Indian Political Thought", "Global Politics", "Human Rights", "Political Sociology", "Public Policy", "Foreign Policy", "Peace Studies", "Electoral Politics", "Political Economy"],
        "BA-ECO": ["Microeconomics", "Macroeconomics", "Public Finance", "International Trade", "Statistics", "Indian Economy", "Development Economics", "Econometrics", "Environmental Economics", "Monetary Economics", "Financial Economics", "Industrial Economics", "Agricultural Economics", "Labor Economics", "Economic History"],
        "BA-SOC": ["Intro to Sociology", "Social Thought", "Social Problems", "Research Methods", "Demography", "Sociology of Family", "Sociology of Religion", "Sociology of Education", "Rural Sociology", "Urban Sociology", "Industrial Sociology", "Political Sociology", "Medical Sociology", "Sociology of Gender", "Criminology"],
        "BC-ACC": ["Financial Accounting", "Cost Accounting", "Corporate Accounting", "Management Accounting", "Auditing", "Advanced Accounting", "Accounting Standards", "Forensic Accounting", "Tax Accounting", "Computerized Accounting"],
        "BC-FIN": ["Financial Management", "Banking", "Investment Analysis", "Financial Markets", "Taxation", "Corporate Finance", "International Finance", "Risk Management", "Portfolio Management", "Financial Services"],
        "BC-TAX": ["Direct Tax", "Indirect Tax", "GST", "Corporate Tax Planning", "Customs", "International Taxation", "Tax Administration", "Wealth Tax", "Business Taxation", "Tax Audit"],
        "BC-BM": ["Principles of Management", "HR Management", "Marketing Management", "Business Environment", "Strategic Management", "Organizational Behavior", "Operations Management", "Business Ethics", "Entrepreneurship", "Business Law"],
        "BC-ITR": ["International Business", "Export Import Procedures", "Global Marketing", "Forex Management", "International Trade Law", "Cross Cultural Management", "International Logistics", "Trade Policy", "Global Finance", "Supply Chain"]
    }
    return topics.get(dept_code, ["Core Subject", "Advanced Topic", "Applied Theory", "Lab Practice", "Research Seminar"])

def generate_subjects(dept, duration_years):
    semesters = duration_years * 2
    base_topics = get_base_topics(dept.code)
    
    subjects_data = []
    modifiers = ["I", "II", "III", "IV", "Fundamentals", "Advanced", "Applied", "Principles of", "Lab"]
    
    used_names = set()
    
    for sem in range(1, semesters + 1):
        for i in range(1, 6): # 5 subjects per sem
            # Construct a unique subject name by combining elements and preventing duplicates
            base_idx = ((sem - 1) * 5 + i - 1) % len(base_topics)
            topic = base_topics[base_idx]
            
            name = topic
            if name in used_names:
                mod = modifiers[((sem - 1) * 5 + i) % len(modifiers)]
                if mod in ["I", "II", "III", "IV"]:
                    name = f"{topic} {mod}"
                elif mod == "Lab":
                    name = f"{topic} Lab"
                else:
                    name = f"{mod} {topic}"
                    
            if name in used_names:
                name = f"{name} Part {sem}"
                
            used_names.add(name)
            
            code = f"{dept.code}-{sem}0{i}"
            
            subjects_data.append({
                "code": code,
                "name": name,
                "semester": sem,
                "credits": 3 if i != 5 else 2,
            })
            
    return subjects_data

def main():
    db = SessionLocal()
    try:
        departments = db.query(Department).filter_by(is_deleted=False).all()
        
        created_count = 0
        updated_count = 0
        
        for dept in departments:
            course = dept.course
            if not course:
                continue
                
            duration_str = course.duration_years or "3"
            try:
                duration = int(duration_str.split()[0])
            except:
                duration = 3
                
            if dept.code == "BT-AS":
                subjects_to_create = generate_subjects(dept, 1) # 1 year = 2 semesters
            else:
                subjects_to_create = generate_subjects(dept, duration)

            for s_data in subjects_to_create:
                existing = db.query(Subject).filter_by(code=s_data["code"]).first()
                if existing:
                    existing.name = s_data["name"]
                    existing.semester = s_data["semester"]
                    existing.credits = s_data["credits"]
                    existing.department_id = dept.id
                    existing.is_deleted = False
                    updated_count += 1
                else:
                    new_sub = Subject(
                        code=s_data["code"],
                        name=s_data["name"],
                        semester=s_data["semester"],
                        credits=s_data["credits"],
                        department_id=dept.id,
                        description=f"Core subject for {dept.name} Semester {s_data['semester']}"
                    )
                    db.add(new_sub)
                    created_count += 1
                    
            db.flush()
            
        db.commit()
        print(f"Successfully seeded subjects! Created: {created_count}, Updated: {updated_count}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
