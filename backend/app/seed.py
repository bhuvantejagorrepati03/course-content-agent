"""
Seed the database with realistic course data for 5 courses.

Usage:
    python -m app.seed
"""
import sys
import logging
from sqlalchemy.orm import Session

from app.database import SessionLocal, create_tables
from app.models.course import Course
from app.models.unit import Unit
from app.models.topic import Topic
from app.models.outcome import CourseOutcome
from app.models.textbook import Textbook
from app.models.mapping import COPOMapping

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


# ── Course seed definitions ───────────────────────────────────────────────────

COURSES = [
    {
        "course_name": "Data Structures",
        "course_code": "CS201",
        "program": "B.Tech CSE",
        "department": "Computer Science & Engineering",
        "year": "II Year",
        "semester": "3rd Semester",
        "regulation": "R23",
        "credits": 4.0,
        "total_hours": 45,
        "description": (
            "Covers fundamental data structures and algorithms including arrays, linked lists, "
            "stacks, queues, trees, and graphs. Students will analyze algorithm complexity and "
            "implement efficient solutions to computational problems."
        ),
        "prerequisites": "Programming in C, Problem Solving & Python Programming",
        "units": [
            {
                "number": 1, "name": "Introduction to Data Structures", "hours": 8,
                "co_mapping": "CO1",
                "topics": [
                    "Introduction to Data Structures",
                    "Abstract Data Types (ADT)",
                    "Arrays – One-dimensional and Multi-dimensional",
                    "Singly Linked List",
                    "Doubly Linked List",
                    "Circular Linked List",
                    "Applications of Linked Lists",
                ],
            },
            {
                "number": 2, "name": "Stacks and Queues", "hours": 8,
                "co_mapping": "CO2",
                "topics": [
                    "Stack ADT – Definition and Operations",
                    "Stack Implementation using Arrays and Linked Lists",
                    "Applications: Expression Evaluation, Infix to Postfix",
                    "Recursion using Stacks",
                    "Queue ADT – Definition and Operations",
                    "Circular Queue",
                    "Priority Queue",
                    "Deque (Double Ended Queue)",
                ],
            },
            {
                "number": 3, "name": "Trees", "hours": 10,
                "co_mapping": "CO3",
                "topics": [
                    "Binary Trees – Terminology and Properties",
                    "Binary Tree Representation",
                    "Binary Search Trees (BST) – Insertion, Deletion, Search",
                    "AVL Trees – Balance Factor and Rotations",
                    "Heap – Min-Heap and Max-Heap",
                    "Heapify and Heap Sort",
                    "Tree Traversals – Inorder, Preorder, Postorder, Level-order",
                    "B-Trees and Applications",
                ],
            },
            {
                "number": 4, "name": "Graphs", "hours": 8,
                "co_mapping": "CO3",
                "topics": [
                    "Graph Terminology – Vertices, Edges, Directed and Undirected Graphs",
                    "Graph Representation – Adjacency Matrix and Adjacency List",
                    "Breadth First Search (BFS)",
                    "Depth First Search (DFS)",
                    "Shortest Path – Dijkstra's Algorithm",
                    "Shortest Path – Bellman-Ford Algorithm",
                    "Minimum Spanning Tree – Prim's Algorithm",
                    "Minimum Spanning Tree – Kruskal's Algorithm",
                ],
            },
            {
                "number": 5, "name": "Sorting and Searching", "hours": 8,
                "co_mapping": "CO4",
                "topics": [
                    "Bubble Sort",
                    "Selection Sort",
                    "Insertion Sort",
                    "Merge Sort",
                    "Quick Sort",
                    "Heap Sort",
                    "Linear Search",
                    "Binary Search",
                    "Hashing and Hash Tables",
                ],
            },
        ],
        "outcomes": [
            {"co": "CO1", "desc": "Understand fundamental data structure concepts and abstract data types.", "bloom": "Understand"},
            {"co": "CO2", "desc": "Analyze and implement linear data structures such as stacks, queues, and linked lists.", "bloom": "Apply"},
            {"co": "CO3", "desc": "Apply tree and graph data structures to solve real-world computational problems.", "bloom": "Apply"},
            {"co": "CO4", "desc": "Evaluate and implement searching and sorting techniques with complexity analysis.", "bloom": "Evaluate"},
        ],
        "textbooks": [
            {"title": "Data Structures Using C", "author": "Reema Thareja", "edition": "2nd Edition", "publisher": "Oxford University Press", "year": "2014", "type": "textbook"},
            {"title": "Data Structures and Algorithm Analysis in C", "author": "Mark Allen Weiss", "edition": "3rd Edition", "publisher": "Pearson Education", "year": "2012", "type": "textbook"},
            {"title": "Introduction to Algorithms", "author": "Cormen, Leiserson, Rivest, Stein", "edition": "3rd Edition", "publisher": "MIT Press", "year": "2009", "type": "reference"},
            {"title": "Fundamentals of Data Structures in C", "author": "Horowitz, Sahni, Anderson-Freed", "edition": "2nd Edition", "publisher": "Universities Press", "year": "2008", "type": "reference"},
        ],
        "mappings": [
            ("CO1", [("PO1", 3), ("PO2", 2), ("PO3", 3), ("PO4", 1), ("PO5", 2), ("PO6", 1), ("PSO1", 3), ("PSO2", 2)]),
            ("CO2", [("PO1", 3), ("PO2", 3), ("PO3", 2), ("PO4", 2), ("PO5", 3), ("PO6", 1), ("PSO1", 3), ("PSO2", 3)]),
            ("CO3", [("PO1", 2), ("PO2", 3), ("PO3", 3), ("PO4", 2), ("PO5", 2), ("PO6", 2), ("PSO1", 2), ("PSO2", 3)]),
            ("CO4", [("PO1", 3), ("PO2", 2), ("PO3", 3), ("PO4", 3), ("PO5", 2), ("PO6", 1), ("PSO1", 3), ("PSO2", 2)]),
        ],
    },

    {
        "course_name": "Database Management Systems",
        "course_code": "CS301",
        "program": "B.Tech CSE",
        "department": "Computer Science & Engineering",
        "year": "II Year",
        "semester": "4th Semester",
        "regulation": "R23",
        "credits": 4.0,
        "total_hours": 45,
        "description": (
            "Comprehensive coverage of relational database design, SQL, normalization, "
            "transaction management, and modern database systems including NoSQL."
        ),
        "prerequisites": "Data Structures, Computer Organization",
        "units": [
            {
                "number": 1, "name": "Introduction to Databases", "hours": 9, "co_mapping": "CO1",
                "topics": [
                    "Database Concepts and Architecture",
                    "Advantages of DBMS over File Systems",
                    "Entity-Relationship (ER) Model",
                    "ER Diagram Notation",
                    "Relational Model – Relations, Tuples, Attributes",
                    "Keys – Primary, Foreign, Candidate, Super",
                    "Relational Algebra",
                ],
            },
            {
                "number": 2, "name": "Structured Query Language", "hours": 10, "co_mapping": "CO2",
                "topics": [
                    "DDL Commands – CREATE, ALTER, DROP",
                    "DML Commands – INSERT, UPDATE, DELETE",
                    "DQL – SELECT with WHERE, ORDER BY, GROUP BY",
                    "Joins – INNER, LEFT, RIGHT, FULL OUTER",
                    "Subqueries and Nested Queries",
                    "Views",
                    "Triggers",
                    "Stored Procedures and Functions",
                ],
            },
            {
                "number": 3, "name": "Normalization", "hours": 8, "co_mapping": "CO3",
                "topics": [
                    "Functional Dependencies",
                    "Inference Rules (Armstrong's Axioms)",
                    "First Normal Form (1NF)",
                    "Second Normal Form (2NF)",
                    "Third Normal Form (3NF)",
                    "Boyce-Codd Normal Form (BCNF)",
                    "Multivalued Dependencies and 4NF",
                ],
            },
            {
                "number": 4, "name": "Transaction Management", "hours": 10, "co_mapping": "CO4",
                "topics": [
                    "Transaction Concept and ACID Properties",
                    "Serializability",
                    "Lock-based Concurrency Control",
                    "Two-Phase Locking Protocol",
                    "Timestamp-based Protocols",
                    "Deadlock Detection and Recovery",
                    "Log-based Recovery",
                    "Shadow Paging",
                ],
            },
            {
                "number": 5, "name": "Advanced Database Systems", "hours": 8, "co_mapping": "CO1,CO4",
                "topics": [
                    "Distributed Databases",
                    "NoSQL Databases – Document, Key-Value, Column, Graph",
                    "MongoDB Basics",
                    "Data Warehousing",
                    "OLAP and Data Mining Concepts",
                    "Database Security and Authorization",
                ],
            },
        ],
        "outcomes": [
            {"co": "CO1", "desc": "Understand database concepts, ER modeling, and the relational model.", "bloom": "Understand"},
            {"co": "CO2", "desc": "Write complex SQL queries for data retrieval and manipulation.", "bloom": "Apply"},
            {"co": "CO3", "desc": "Apply normalization techniques to design efficient relational schemas.", "bloom": "Apply"},
            {"co": "CO4", "desc": "Analyze transaction management, concurrency control, and recovery techniques.", "bloom": "Analyze"},
        ],
        "textbooks": [
            {"title": "Database System Concepts", "author": "Silberschatz, Korth, Sudarshan", "edition": "7th Edition", "publisher": "McGraw-Hill", "year": "2020", "type": "textbook"},
            {"title": "Fundamentals of Database Systems", "author": "Ramez Elmasri, Shamkant Navathe", "edition": "7th Edition", "publisher": "Pearson", "year": "2017", "type": "reference"},
        ],
        "mappings": [
            ("CO1", [("PO1", 3), ("PO2", 2), ("PO3", 2), ("PO4", 1), ("PO5", 2), ("PO6", 1), ("PSO1", 3), ("PSO2", 2)]),
            ("CO2", [("PO1", 3), ("PO2", 3), ("PO3", 3), ("PO4", 2), ("PO5", 3), ("PO6", 1), ("PSO1", 3), ("PSO2", 3)]),
            ("CO3", [("PO1", 2), ("PO2", 3), ("PO3", 2), ("PO4", 2), ("PO5", 2), ("PO6", 2), ("PSO1", 2), ("PSO2", 2)]),
            ("CO4", [("PO1", 3), ("PO2", 2), ("PO3", 3), ("PO4", 3), ("PO5", 2), ("PO6", 2), ("PSO1", 3), ("PSO2", 3)]),
        ],
    },

    {
        "course_name": "Object Oriented Programming",
        "course_code": "CS202",
        "program": "B.Tech CSE",
        "department": "Computer Science & Engineering",
        "year": "II Year",
        "semester": "3rd Semester",
        "regulation": "R23",
        "credits": 3.0,
        "total_hours": 40,
        "description": (
            "Covers the object-oriented programming paradigm using Java/C++: classes, objects, "
            "inheritance, polymorphism, encapsulation, exception handling, and design patterns."
        ),
        "prerequisites": "Programming in C",
        "units": [
            {
                "number": 1, "name": "Classes and Objects", "hours": 8, "co_mapping": "CO1",
                "topics": [
                    "Introduction to Object-Oriented Programming",
                    "Classes and Objects",
                    "Data Members and Member Functions",
                    "Constructors and Destructors",
                    "Static Members",
                    "Friend Functions and Classes",
                ],
            },
            {
                "number": 2, "name": "Inheritance and Polymorphism", "hours": 9, "co_mapping": "CO2",
                "topics": [
                    "Types of Inheritance – Single, Multiple, Multilevel",
                    "Method Overloading",
                    "Method Overriding",
                    "Virtual Functions",
                    "Abstract Classes and Pure Virtual Functions",
                    "Runtime Polymorphism",
                ],
            },
            {
                "number": 3, "name": "Encapsulation and Abstraction", "hours": 7, "co_mapping": "CO1",
                "topics": [
                    "Access Modifiers – public, private, protected",
                    "Data Hiding and Encapsulation",
                    "Abstract Classes",
                    "Interfaces",
                    "Packages and Namespaces",
                ],
            },
            {
                "number": 4, "name": "Exception Handling and I/O", "hours": 8, "co_mapping": "CO3",
                "topics": [
                    "Exception Handling Mechanisms – try, catch, throw",
                    "Built-in Exceptions",
                    "User-defined Exceptions",
                    "File I/O Streams",
                    "Serialization",
                ],
            },
            {
                "number": 5, "name": "Design Patterns", "hours": 8, "co_mapping": "CO4",
                "topics": [
                    "Introduction to Design Patterns",
                    "Creational Patterns – Singleton, Factory",
                    "Structural Patterns – Adapter, Decorator",
                    "Behavioral Patterns – Observer, Strategy",
                    "SOLID Principles",
                ],
            },
        ],
        "outcomes": [
            {"co": "CO1", "desc": "Understand OOP concepts including classes, objects, and encapsulation.", "bloom": "Understand"},
            {"co": "CO2", "desc": "Apply inheritance and polymorphism to design reusable software.", "bloom": "Apply"},
            {"co": "CO3", "desc": "Implement exception handling and file I/O mechanisms effectively.", "bloom": "Apply"},
            {"co": "CO4", "desc": "Design software using standard object-oriented design patterns.", "bloom": "Create"},
        ],
        "textbooks": [
            {"title": "Object Oriented Programming with C++", "author": "E. Balagurusamy", "edition": "6th Edition", "publisher": "McGraw-Hill", "year": "2013", "type": "textbook"},
            {"title": "The Java Programming Language", "author": "James Gosling", "edition": "4th Edition", "publisher": "Addison-Wesley", "year": "2005", "type": "reference"},
        ],
        "mappings": [
            ("CO1", [("PO1", 3), ("PO2", 2), ("PO3", 2), ("PO4", 1), ("PO5", 1), ("PO6", 1), ("PSO1", 3), ("PSO2", 2)]),
            ("CO2", [("PO1", 3), ("PO2", 3), ("PO3", 3), ("PO4", 2), ("PO5", 2), ("PO6", 1), ("PSO1", 3), ("PSO2", 3)]),
            ("CO3", [("PO1", 2), ("PO2", 2), ("PO3", 3), ("PO4", 2), ("PO5", 2), ("PO6", 2), ("PSO1", 2), ("PSO2", 2)]),
            ("CO4", [("PO1", 3), ("PO2", 3), ("PO3", 3), ("PO4", 3), ("PO5", 3), ("PO6", 2), ("PSO1", 3), ("PSO2", 3)]),
        ],
    },

    {
        "course_name": "Operating Systems",
        "course_code": "CS401",
        "program": "B.Tech CSE",
        "department": "Computer Science & Engineering",
        "year": "III Year",
        "semester": "5th Semester",
        "regulation": "R23",
        "credits": 4.0,
        "total_hours": 45,
        "description": (
            "Principles of modern operating systems: process management, memory management, "
            "file systems, synchronization, and security."
        ),
        "prerequisites": "Computer Organization, Data Structures",
        "units": [
            {
                "number": 1, "name": "Process Management", "hours": 9, "co_mapping": "CO1",
                "topics": [
                    "Operating System Overview and Types",
                    "Process Concept and Process States",
                    "Process Control Block (PCB)",
                    "CPU Scheduling – FCFS, SJF, Round Robin, Priority",
                    "Threads and Multithreading Models",
                    "Inter-Process Communication (IPC)",
                ],
            },
            {
                "number": 2, "name": "Process Synchronization", "hours": 9, "co_mapping": "CO2",
                "topics": [
                    "Critical Section Problem",
                    "Peterson's Solution",
                    "Semaphores and Mutex",
                    "Classic Problems – Dining Philosophers, Producer-Consumer",
                    "Deadlock – Definition and Conditions",
                    "Deadlock Prevention and Avoidance",
                    "Deadlock Detection and Recovery",
                ],
            },
            {
                "number": 3, "name": "Memory Management", "hours": 9, "co_mapping": "CO3",
                "topics": [
                    "Contiguous Memory Allocation",
                    "Fragmentation – Internal and External",
                    "Paging",
                    "Segmentation",
                    "Virtual Memory and Demand Paging",
                    "Page Replacement Algorithms – FIFO, LRU, Optimal",
                    "Thrashing",
                ],
            },
            {
                "number": 4, "name": "File System", "hours": 9, "co_mapping": "CO4",
                "topics": [
                    "File Concept and File Operations",
                    "File Access Methods",
                    "Directory Structure",
                    "File System Implementation",
                    "Allocation Methods – Contiguous, Linked, Indexed",
                    "Free Space Management",
                ],
            },
            {
                "number": 5, "name": "I/O Systems and Security", "hours": 9, "co_mapping": "CO4",
                "topics": [
                    "I/O Hardware and Software",
                    "Disk Scheduling – FCFS, SSTF, SCAN, C-SCAN",
                    "RAID Levels",
                    "OS Security – Authentication and Authorization",
                    "Access Control Lists",
                    "Malware and Intrusion Detection",
                ],
            },
        ],
        "outcomes": [
            {"co": "CO1", "desc": "Understand OS structure, process states, and CPU scheduling algorithms.", "bloom": "Understand"},
            {"co": "CO2", "desc": "Analyze deadlock conditions and apply prevention and avoidance strategies.", "bloom": "Analyze"},
            {"co": "CO3", "desc": "Implement memory management techniques including paging and virtual memory.", "bloom": "Apply"},
            {"co": "CO4", "desc": "Understand file system structures, I/O management, and OS security.", "bloom": "Understand"},
        ],
        "textbooks": [
            {"title": "Operating System Concepts", "author": "Silberschatz, Galvin, Gagne", "edition": "10th Edition", "publisher": "Wiley", "year": "2018", "type": "textbook"},
            {"title": "Modern Operating Systems", "author": "Andrew S. Tanenbaum", "edition": "4th Edition", "publisher": "Pearson", "year": "2015", "type": "reference"},
        ],
        "mappings": [
            ("CO1", [("PO1", 3), ("PO2", 2), ("PO3", 2), ("PO4", 1), ("PO5", 2), ("PO6", 1), ("PSO1", 3), ("PSO2", 2)]),
            ("CO2", [("PO1", 3), ("PO2", 3), ("PO3", 3), ("PO4", 2), ("PO5", 2), ("PO6", 1), ("PSO1", 2), ("PSO2", 2)]),
            ("CO3", [("PO1", 2), ("PO2", 3), ("PO3", 3), ("PO4", 3), ("PO5", 2), ("PO6", 2), ("PSO1", 3), ("PSO2", 3)]),
            ("CO4", [("PO1", 3), ("PO2", 2), ("PO3", 2), ("PO4", 2), ("PO5", 2), ("PO6", 1), ("PSO1", 3), ("PSO2", 2)]),
        ],
    },

    {
        "course_name": "Computer Networks",
        "course_code": "CS402",
        "program": "B.Tech CSE",
        "department": "Computer Science & Engineering",
        "year": "III Year",
        "semester": "5th Semester",
        "regulation": "R23",
        "credits": 4.0,
        "total_hours": 45,
        "description": (
            "Comprehensive study of computer networking: OSI and TCP/IP models, data link protocols, "
            "routing algorithms, transport layer, application protocols, and network security."
        ),
        "prerequisites": "Digital Electronics, Data Communications",
        "units": [
            {
                "number": 1, "name": "Introduction to Networks", "hours": 8, "co_mapping": "CO1",
                "topics": [
                    "Network Fundamentals and Classifications",
                    "Network Topologies",
                    "OSI Reference Model – 7 Layers",
                    "TCP/IP Protocol Suite",
                    "Transmission Media – Guided and Unguided",
                    "Switching – Circuit, Packet, Message",
                ],
            },
            {
                "number": 2, "name": "Data Link Layer", "hours": 9, "co_mapping": "CO2",
                "topics": [
                    "Framing Methods",
                    "Error Detection – CRC, Checksum",
                    "Error Correction – Hamming Code",
                    "Flow Control – Stop-and-Wait, Sliding Window",
                    "ARQ Protocols – Go-Back-N, Selective Repeat",
                    "MAC Protocols – ALOHA, CSMA/CD",
                    "Ethernet (IEEE 802.3)",
                    "VLANs and Switches",
                ],
            },
            {
                "number": 3, "name": "Network Layer", "hours": 9, "co_mapping": "CO3",
                "topics": [
                    "IP Addressing – IPv4 and Subnetting",
                    "Classless Addressing (CIDR)",
                    "Routing Algorithms – Distance Vector, Link State",
                    "RIP, OSPF, and BGP Protocols",
                    "NAT (Network Address Translation)",
                    "ICMP",
                    "IPv6",
                ],
            },
            {
                "number": 4, "name": "Transport Layer", "hours": 10, "co_mapping": "CO4",
                "topics": [
                    "Transport Layer Services",
                    "UDP – Connectionless Service",
                    "TCP – Connection-Oriented Service",
                    "TCP Handshaking and Connection Management",
                    "Flow Control in TCP",
                    "Congestion Control – Slow Start, AIMD",
                    "Socket Programming Basics",
                ],
            },
            {
                "number": 5, "name": "Application Layer and Security", "hours": 9, "co_mapping": "CO4",
                "topics": [
                    "DNS – Domain Name System",
                    "HTTP and HTTPS",
                    "SMTP, POP3, IMAP",
                    "FTP and SSH",
                    "Network Security Fundamentals",
                    "SSL/TLS Protocol",
                    "Firewalls and IDS/IPS",
                ],
            },
        ],
        "outcomes": [
            {"co": "CO1", "desc": "Understand the OSI and TCP/IP reference models and their protocol layers.", "bloom": "Understand"},
            {"co": "CO2", "desc": "Apply data link layer protocols and LAN technologies.", "bloom": "Apply"},
            {"co": "CO3", "desc": "Analyze network layer routing algorithms and IP addressing schemes.", "bloom": "Analyze"},
            {"co": "CO4", "desc": "Understand transport layer services and application layer protocols.", "bloom": "Understand"},
        ],
        "textbooks": [
            {"title": "Computer Networks", "author": "Andrew S. Tanenbaum", "edition": "5th Edition", "publisher": "Pearson", "year": "2011", "type": "textbook"},
            {"title": "Computer Networking: A Top-Down Approach", "author": "James F. Kurose, Keith W. Ross", "edition": "8th Edition", "publisher": "Pearson", "year": "2021", "type": "reference"},
        ],
        "mappings": [
            ("CO1", [("PO1", 3), ("PO2", 2), ("PO3", 2), ("PO4", 1), ("PO5", 2), ("PO6", 1), ("PSO1", 3), ("PSO2", 2)]),
            ("CO2", [("PO1", 2), ("PO2", 3), ("PO3", 3), ("PO4", 2), ("PO5", 3), ("PO6", 1), ("PSO1", 2), ("PSO2", 2)]),
            ("CO3", [("PO1", 3), ("PO2", 3), ("PO3", 3), ("PO4", 3), ("PO5", 2), ("PO6", 2), ("PSO1", 3), ("PSO2", 3)]),
            ("CO4", [("PO1", 3), ("PO2", 2), ("PO3", 2), ("PO4", 2), ("PO5", 2), ("PO6", 1), ("PSO1", 3), ("PSO2", 2)]),
        ],
    },
]


# ── Seeding logic ─────────────────────────────────────────────────────────────

def seed_course(data: dict, db: Session) -> Course:
    # Skip if already seeded (check regulation+code composite)
    existing = db.query(Course).filter(
        Course.regulation == data["regulation"],
        Course.course_code == data["course_code"],
    ).first()
    if existing:
        logger.info("Skipping existing course: %s", data["course_code"])
        return existing

    course = Course(
        course_name=data["course_name"],
        course_code=data["course_code"],
        program=data["program"],
        branch=data.get("branch", "CSE"),
        department=data["department"],
        year=data["year"],
        semester=data["semester"],
        regulation=data["regulation"],
        credits=data["credits"],
        total_hours=data["total_hours"],
        description=data.get("description"),
        prerequisites=data.get("prerequisites"),
        source_type="seed",
    )
    db.add(course)
    db.flush()

    for unit_data in data["units"]:
        unit = Unit(
            course_id=course.id,
            unit_number=unit_data["number"],
            unit_name=unit_data["name"],
            hours=unit_data["hours"],
            co_mapping=unit_data.get("co_mapping"),
        )
        db.add(unit)
        db.flush()
        for order, topic_name in enumerate(unit_data["topics"]):
            db.add(Topic(unit_id=unit.id, topic_name=topic_name, topic_order=order))

    for co_data in data["outcomes"]:
        db.add(CourseOutcome(
            course_id=course.id,
            co_number=co_data["co"],
            description=co_data["desc"],
            bloom_level=co_data.get("bloom"),
        ))

    for book in data["textbooks"]:
        db.add(Textbook(
            course_id=course.id,
            title=book["title"],
            author=book["author"],
            edition=book.get("edition"),
            publisher=book.get("publisher"),
            year=book.get("year"),
            book_type=book.get("type", "textbook"),
        ))

    for co_num, po_pairs in data["mappings"]:
        for po_num, value in po_pairs:
            db.add(COPOMapping(
                course_id=course.id,
                co_number=co_num,
                po_number=po_num,
                value=value,
            ))

    db.commit()
    logger.info("Seeded course: %s — %s", course.course_code, course.course_name)
    return course


def run_seed():
    create_tables()
    db: Session = SessionLocal()
    try:
        for course_data in COURSES:
            seed_course(course_data, db)
        logger.info("Seed completed — %d courses available", len(COURSES))
    except Exception as exc:
        logger.exception("Seed failed: %s", exc)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
