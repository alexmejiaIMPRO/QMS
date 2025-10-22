import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.auth import hash_password
from database.connection import get_db
from config import EntityType
import uuid
from datetime import datetime, timedelta
import random


def seed_users():
    """Create users with different roles"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    users = [
        {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "password": "admin123",
            "role": "Admin",
        },
        {
            "id": str(uuid.uuid4()),
            "username": "john_engineer",
            "password": "engineer123",
            "role": "Engineer",
        },
        {
            "id": str(uuid.uuid4()),
            "username": "sarah_supervisor",
            "password": "supervisor123",
            "role": "Supervisor",
        },
        {
            "id": str(uuid.uuid4()),
            "username": "mike_operator",
            "password": "operator123",
            "role": "Operator",
        },
        {
            "id": str(uuid.uuid4()),
            "username": "lisa_engineer",
            "password": "engineer123",
            "role": "Engineer",
        },
        {
            "id": str(uuid.uuid4()),
            "username": "tom_operator",
            "password": "operator123",
            "role": "Operator",
        },
    ]

    for user in users:
        try:
            c.execute(
                """
                INSERT INTO users (id, username, password_hash, role, is_active)
                VALUES (?, ?, ?, ?, 1)
            """,
                (
                    user["id"],
                    user["username"],
                    hash_password(user["password"]),
                    user["role"],
                ),
            )
            print(f"Created user: {user['username']} (Role: {user['role']})")
        except Exception as e:
            print(f"User {user['username']} already exists or error: {e}")

    conn.commit()
    conn.close()
    return users


def seed_entities():
    """Seed all entity tables with mock data"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    entities_data = {
        EntityType.EMPLOYEES: [
            "Li Yaojie",
            "Zhou Liying",
            "Vega Segura, Emmanuel",
            "Rodriguez Hernandez, Braulio",
            "Hernandez Guerrero, Jose Victor",
            "Gutierrez, Jonathan",
            "Esteva Luis, Jonathan Vicente",
            "Rodriguez Lopez, Leonardo Daniel",
            "Rocha Sanchez, David Emmanuel",
            "Lopez Perez, Nataly Raquel",
            "Aguilera Salas, Miguel Naim",
            "De La Luz Octaviano, Eric",
            "Rodriguez Padron, Diana Isela",
            "Covarrubias Gonzalez, Gael Antonio",
            "Martinez Gutierrez, Juan Misael",
            "Colunga Mendez, Tadeo Gael",
            "Rivera Quezada, Erik",
            "Herrera Zuñiga, Cesar Carmelo",
            "Miranda Cuevas, Fernando Enrique",
            "Infante Dimas, Karina Lizbeth",
            "Juarez Uribe, Juan Alan",
            "Jalomo Gone, Cesar Omar",
            "Aviles Segura, Liliana",
            "Fuentes Fuentes, Angelica Maria",
            "Niño Rodriguez, Luis Antonio",
            "Martinez Vazquez, Jonathan Orlando",
            "Jasso Silva, Lesly Alondra",
            "Becerra Mendez, Elizabeth",
            "Ornelas Flores, Gerardo",
            "Garcia Ovalle, Juan Gustavo",
            "Marquez Bravo, Adriana",
            "Hernandez Gaspar, Rocio Jhoana",
            "Hernandez Reyes, Amado",
            "Maya Salas, Valeria",
            "Castro Sanchez, Olga Carolina",
            "Oliva Gutierrez, Ma Del Carmen",
            "Torres Silva, Ximena Sarahi",
            "Garcia Ovalle, Victor Manuel",
            "Rodriguez Salazar, Jose Enrique",
            "Alvarado Salazar, Paola Guadalupe",
            "Silva Lopez, Sonia Alejandra",
            "Ramos Hernandez, Angel Josue",
            "Ramirez Campos, Erick Adolfo",
            "Gallegos Ruedas, Patricia Lili",
            "Romero Olaya, Cesar",
            "Bravo Lopez, Victor Javier",
            "Mora Aviles, Gloria Esmeralda",
            "Orozco Alvarado, Jesus Alberto",
            "Martinez Martinez, Rosario De Jesus",
            "Cardenas Lopez, Jesus Alberto",
            "Martinez Segura, Sandra",
            "Lopez Moreno, Sergio Eduardo",
            "Jalomo Garcia, Efren",
            "Gonzalez Hernandez, Carlos Eduardo",
            "Morales Argot, Angel Giovanni",
            "Ramirez Elias, Vanessa",
            "Sun Huaqiao",
            "Yang Daquan",
            "Zheng Leilei",
            "Yu Zhu",
            "Hu Kaisong",
            "Yuan Lei",
            "Kong Leifeng",
            "Guan Haobin",
            "Zhang Wei",
            "Xiao Gang",
            "Chang Yong",
        ],
        EntityType.WORKCENTERS: [
            "WC-001 Assembly",
            "WC-002 Machining",
            "WC-003 Welding",
            "WC-004 Painting",
            "WC-005 Quality Control",
            "WC-006 Packaging",
        ],
        EntityType.CUSTOMERS: [
            "Ford Motor Company",
            "General Motors",
            "Tesla Inc",
            "Toyota Motors",
            "Honda Manufacturing",
            "BMW Group",
        ],
        EntityType.PARTNUMBERS: [
            "9151355",
"5073135-101",
"10101B-518",
"10101C-744",
"10101B-514",
"5153060-101",
"5073134-101",
"5203024-101",
"5133103-101",
"10101C-732",
"1-01-050(09)",
"5203118-101",
"5093208-102",
"336-0035-01",
"10101B-572",
"2823488-101",
"5193156-101",
"436-890",
"488-133",
"A1-379-1",
"230-1056-01",
"5113269-101",
"5113267-101",
"5203258-101",
"5043158-101",
"5103200-101",
"5073180-101",
"5153042-101",
"5133061-101",
"5043152-101",
"5043103-101",
"5133052-102",
"2793957-101",
"5203312-101",
"3171539-113",
"2305449-1",
"5093782-102",
"5093913-102",
"3171539-2",
"3171539-2-1",
"2305449-1",
"5193467-101",
"5203028-101",
"5203023-101",
"5203083-101",
"2093123-101",
"26538-ANW",
"A3-766-1",
"A3-769-1",
"5193468-101",
"5023008-1",
"5023008-101",
"5143020-101",
"5203054-101",
"5203062-101",
"5193418-101",
"2103120-101",
"5203086-101",
"5203086-101",
"5193357-101",
"5193215-101",
"5193082-102",
"5193082-101",
"5073121-101",
"5203288-101",
"5203263-101",
"5193354-101",
"5093243-102",
"880420-103",
"7203012-101",
"5093831-102",
"7203013-101",
"5193032-101",
"5113117-101",
"24828-02",
"24827-02",
"27044",
"476181-101",
"617553-101",
"617552-101",
"26480",
"617562-101",
"617563-101",
"27145",
"617151-101",
"27440",
"27441",
"616539-1",
"24823-02",
"24824-02",
"624420-1",
"624432-1",
"A1-1352-2",
"A1-1473-1",
"A1-1474-1",
"A1-1602-1",
"A1-1600-1",
"A1-1601-1",
"2200007-101",
"A1-1060-1",
"A9-374-2",
"A9-384-2",
"6122145",
"5163010-101",
"5153068-101",
"10101-1",
"5173063-101",
"10101C-749",
"5203025-101",
"10101C-724",
"5133104-101",
"5203112-101",
"5153043-101",
"5093207-101",
"5133062-101",
"5203119-101",
"5093621-101",
"10101C-731",
"5153053-101",
"5113270-101",
"5043104-101",
"331-0013-01",
"336-0038-01",
"5113268-101",
"5073126-101",
"2083314-101",
"1-01-09",
"436-889",
"10101B-571",
"332-0019-01",
"2793956-101",
"332-0008-01",
"10101B-511",
"230-1056-01",
"332-0100-01",
"10101C-712",
"488-120",
"A1-380-1",
"5043159-104",
"5153129-101",
"5073181-101",
"5133053-102",
"5203260-101",
"5203313-101",
"5203314-101"
        ],
        EntityType.INSPECTION_ITEMS: [
            "Dimensional Check",
            "Visual Inspection",
            "Hardness Test",
            "Surface Finish",
            "Thread Inspection",
            "Coating Thickness",
        ],
        EntityType.PREPARED_BY: [
            "QC Inspector 1",
            "QC Inspector 2",
            "QC Inspector 3",
            "Lead Inspector",
            "Quality Manager",
        ],
        EntityType.CAR_TYPES: [
            "Corrective Action",
            "Preventive Action",
            "Process Improvement",
            "Design Change",
            "Supplier Issue",
        ],
        EntityType.DISPOSITIONS: [
            "Use As Is",
            "Rework",
            "Scrap",
            "Return to Supplier",
            "Engineering Review Required",
        ],
        EntityType.FAILURE_CODES: [
            "FC-001 Dimensional",
            "FC-002 Surface Defect",
            "FC-003 Material",
            "FC-004 Process",
            "FC-005 Handling Damage",
            "FC-006 Design",
        ],
        EntityType.AREAS: [
            "Production Floor",
            "Quality Lab",
            "Warehouse",
            "Shipping/Receiving",
            "Engineering",
        ],
        EntityType.LEVELS: ["Critical", "Major", "Minor", "Observation"],
        EntityType.CALIBRATIONS: [
            "Micrometer",
            "Caliper",
            "Height Gauge",
            "CMM",
            "Hardness Tester",
            "Surface Roughness Tester",
        ],
    }

    employee_counter = 1001

    for entity_type, items in entities_data.items():
        for item in items:
            try:
                entity_id = str(uuid.uuid4())
                
                if entity_type == EntityType.EMPLOYEES:
                    employee_number = f"EMP-{employee_counter}"
                    c.execute(
                        f"""
                        INSERT INTO {entity_type.value} (id, name, employee_number, is_active)
                        VALUES (?, ?, ?, 1)
                    """,
                        (entity_id, item, employee_number),
                    )
                    print(f"Created {entity_type.value}: {item} (#{employee_number})")
                    employee_counter += 1
                else:
                    c.execute(
                        f"""
                        INSERT INTO {entity_type.value} (id, name, is_active)
                        VALUES (?, ?, 1)
                    """,
                        (entity_id, item),
                    )
                    print(f"Created {entity_type.value}: {item}")
            except Exception as e:
                print(f"Entity {item} already exists or error: {e}")

    conn.commit()
    conn.close()


def seed_dmt_records(users):
    """Create mock DMT records with different statuses and assignments"""
    db = get_db()
    conn = db.get_connection()
    c = conn.cursor()

    # Get current report counter
    c.execute("SELECT next_number FROM report_counter WHERE id = 1")
    result = c.fetchone()
    report_number = result[0] if result else 1000

    statuses = ["open", "in_progress", "closed"]
    work_centers = ["WC-001 Assembly", "WC-002 Machining", "WC-003 Welding"]
    part_numbers = ["PN-12345-A", "PN-23456-B", "PN-34567-C"]
    customers = ["Ford Motor Company", "General Motors", "Tesla Inc"]

    employees = [
        "Li Yaojie",
        "Zhou Liying",
        "Vega Segura, Emmanuel",
        "Rodriguez Hernandez, Braulio",
        "Hernandez Guerrero, Jose Victor",
        "Gutierrez, Jonathan",
        "Esteva Luis, Jonathan Vicente",
        "Rodriguez Lopez, Leonardo Daniel",
        "Rocha Sanchez, David Emmanuel",
    ]

    
    # Update the counter
    c.execute(
        "UPDATE report_counter SET next_number = ? WHERE id = 1", (report_number,)
    )

    conn.commit()
    conn.close()


def main():
    """Main seeding function"""
    print("=" * 60)
    print("Starting database seeding...")
    print("=" * 60)

    print("\n1. Seeding Users...")
    users = seed_users()

    print("\n2. Seeding Entity Tables...")
    seed_entities()

    print("\n3. Seeding DMT Records...")
    seed_dmt_records(users)

    print("\n" + "=" * 60)
    print("Database seeding completed successfully!")
    print("=" * 60)
    print("\nDefault Login Credentials:")
    print("-" * 60)
    print("Admin:      username: admin          password: admin123")
    print("Engineer:   username: john_engineer  password: engineer123")
    print("Supervisor: username: sarah_supervisor password: supervisor123")
    print("Operator:   username: mike_operator  password: operator123")
    print("-" * 60)


if __name__ == "__main__":
    main()
