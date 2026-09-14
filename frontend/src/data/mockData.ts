import type { Course, Textbook, ReferenceBook, SyllabusDocument, AnalyticsData } from '../types';

// ============================================================
// MOCK DATA — Replace with API calls via service layer
// ============================================================

export const mockCourses: Course[] = [
  {
    id: 'cs201',
    name: 'Data Structures',
    code: 'CS201',
    program: 'B.Tech CSE',
    department: 'Computer Science & Engineering',
    year: 'II Year',
    semester: '3rd Semester',
    regulation: 'R23',
    credits: 4,
    totalHours: 45,
    description:
      'This course covers fundamental data structures and algorithms including arrays, linked lists, stacks, queues, trees, and graphs. Students will analyze algorithm complexity and implement efficient solutions to computational problems.',
    prerequisites: ['Programming in C', 'Problem Solving & Python Programming'],
    status: 'indexed',
    uploadedAt: '2024-01-15T09:00:00Z',
    syllabusFile: 'DataStructures_R23.pdf',
    courseOutcomes: [
      { id: 'cs201-co1', code: 'CO1', description: 'Understand fundamental data structure concepts and abstract data types.', bloomLevel: 'Understand' },
      { id: 'cs201-co2', code: 'CO2', description: 'Analyze and implement linear data structures such as stacks and queues.', bloomLevel: 'Apply' },
      { id: 'cs201-co3', code: 'CO3', description: 'Apply tree and graph data structures to solve real-world problems.', bloomLevel: 'Apply' },
      { id: 'cs201-co4', code: 'CO4', description: 'Evaluate and implement searching and sorting techniques with complexity analysis.', bloomLevel: 'Evaluate' },
    ],
    units: [
      {
        id: 'cs201-u1', number: 1, title: 'Introduction to Data Structures', hours: 8, coMapping: ['CO1'],
        description: 'Fundamentals of data structures, ADTs, and array-based implementations.',
        topics: [
          { id: 't1', title: 'Introduction to Data Structures', subtopics: ['Definition', 'Classification', 'Operations'] },
          { id: 't2', title: 'Abstract Data Types', subtopics: ['ADT Concept', 'List ADT'] },
          { id: 't3', title: 'Arrays', subtopics: ['One-dimensional arrays', 'Multi-dimensional arrays', 'Array operations'] },
          { id: 't4', title: 'Linked Lists', subtopics: ['Singly Linked List', 'Doubly Linked List', 'Circular Linked List'] },
          { id: 't5', title: 'Applications of Linked Lists' },
        ],
      },
      {
        id: 'cs201-u2', number: 2, title: 'Stacks and Queues', hours: 8, coMapping: ['CO2'],
        description: 'Linear data structures with restricted access — stacks and various queue types.',
        topics: [
          { id: 't6', title: 'Stack ADT', subtopics: ['Definition', 'Stack operations: push, pop, peek'] },
          { id: 't7', title: 'Stack Operations and Applications', subtopics: ['Expression evaluation', 'Infix to postfix conversion', 'Recursion'] },
          { id: 't8', title: 'Queue ADT', subtopics: ['Definition', 'Enqueue and Dequeue'] },
          { id: 't9', title: 'Circular Queue', subtopics: ['Implementation', 'Advantages over linear queue'] },
          { id: 't10', title: 'Priority Queue', subtopics: ['Min heap', 'Max heap', 'Applications'] },
          { id: 't11', title: 'Deque (Double Ended Queue)' },
        ],
      },
      {
        id: 'cs201-u3', number: 3, title: 'Trees', hours: 10, coMapping: ['CO3'],
        description: 'Hierarchical data structures including binary trees, BSTs, AVL trees, and heaps.',
        topics: [
          { id: 't12', title: 'Binary Trees', subtopics: ['Terminology', 'Properties', 'Representation'] },
          { id: 't13', title: 'Binary Search Trees', subtopics: ['Insertion', 'Deletion', 'Search operations'] },
          { id: 't14', title: 'AVL Trees', subtopics: ['Balance factor', 'Rotations', 'Insertion and deletion'] },
          { id: 't15', title: 'Heap', subtopics: ['Min-heap', 'Max-heap', 'Heapify', 'Heap sort'] },
          { id: 't16', title: 'Tree Traversals', subtopics: ['Inorder', 'Preorder', 'Postorder', 'Level-order'] },
          { id: 't17', title: 'B-Trees and Applications' },
        ],
      },
      {
        id: 'cs201-u4', number: 4, title: 'Graphs', hours: 8, coMapping: ['CO3'],
        description: 'Graph theory, representations, and traversal algorithms.',
        topics: [
          { id: 't18', title: 'Graph Terminology', subtopics: ['Vertices, Edges', 'Directed and undirected graphs'] },
          { id: 't19', title: 'Graph Representation', subtopics: ['Adjacency matrix', 'Adjacency list'] },
          { id: 't20', title: 'Breadth First Search (BFS)', subtopics: ['Algorithm', 'Complexity', 'Applications'] },
          { id: 't21', title: 'Depth First Search (DFS)', subtopics: ['Algorithm', 'Complexity', 'Applications'] },
          { id: 't22', title: 'Shortest Path Algorithms', subtopics: ["Dijkstra's algorithm", 'Bellman-Ford'] },
          { id: 't23', title: 'Minimum Spanning Tree', subtopics: ["Prim's algorithm", "Kruskal's algorithm"] },
        ],
      },
      {
        id: 'cs201-u5', number: 5, title: 'Sorting and Searching', hours: 8, coMapping: ['CO4'],
        description: 'Classical sorting and searching techniques with time complexity analysis.',
        topics: [
          { id: 't24', title: 'Bubble Sort', subtopics: ['Algorithm', 'Time complexity O(n²)'] },
          { id: 't25', title: 'Selection Sort', subtopics: ['Algorithm', 'Comparison with Bubble Sort'] },
          { id: 't26', title: 'Insertion Sort', subtopics: ['Algorithm', 'Best and worst cases'] },
          { id: 't27', title: 'Merge Sort', subtopics: ['Divide and conquer', 'Time complexity O(n log n)'] },
          { id: 't28', title: 'Quick Sort', subtopics: ['Partition scheme', 'Average complexity O(n log n)'] },
          { id: 't29', title: 'Searching Techniques', subtopics: ['Linear search', 'Binary search', 'Hashing'] },
        ],
      },
    ],
    textbooks: [
      { id: 'tb1', title: 'Data Structures Using C', author: 'Reema Thareja', edition: '2nd Edition', publisher: 'Oxford University Press', year: '2014', courseIds: ['cs201'], unitRelevance: [1, 2, 3, 4, 5], type: 'textbook' },
      { id: 'tb2', title: 'Data Structures and Algorithm Analysis in C', author: 'Mark Allen Weiss', edition: '3rd Edition', publisher: 'Pearson Education', year: '2012', courseIds: ['cs201'], unitRelevance: [1, 2, 3, 4, 5], type: 'textbook' },
    ],
    referenceBooks: [
      { id: 'rb1', title: 'Introduction to Algorithms', author: 'Cormen, Leiserson, Rivest, Stein', edition: '3rd Edition', publisher: 'MIT Press', year: '2009', courseIds: ['cs201'], type: 'reference' },
      { id: 'rb2', title: 'Fundamentals of Data Structures in C', author: 'Horowitz, Sahni, Anderson-Freed', edition: '2nd Edition', publisher: 'Universities Press', year: '2008', courseIds: ['cs201'], type: 'reference' },
    ],
    mappings: [
      { courseOutcomeId: 'CO1', mappings: { PO1: 3, PO2: 2, PO3: 3, PO4: 1, PO5: 2, PO6: 1, PSO1: 3, PSO2: 2 } },
      { courseOutcomeId: 'CO2', mappings: { PO1: 3, PO2: 3, PO3: 2, PO4: 2, PO5: 3, PO6: 1, PSO1: 3, PSO2: 3 } },
      { courseOutcomeId: 'CO3', mappings: { PO1: 2, PO2: 3, PO3: 3, PO4: 2, PO5: 2, PO6: 2, PSO1: 2, PSO2: 3 } },
      { courseOutcomeId: 'CO4', mappings: { PO1: 3, PO2: 2, PO3: 3, PO4: 3, PO5: 2, PO6: 1, PSO1: 3, PSO2: 2 } },
    ],
  },
  {
    id: 'cs301',
    name: 'Database Management Systems',
    code: 'CS301',
    program: 'B.Tech CSE',
    department: 'Computer Science & Engineering',
    year: 'II Year',
    semester: '4th Semester',
    regulation: 'R23',
    credits: 4,
    totalHours: 45,
    description: 'Comprehensive coverage of relational database design, SQL, normalization, transaction management, and modern database systems.',
    prerequisites: ['Data Structures', 'Computer Organization'],
    status: 'indexed',
    uploadedAt: '2024-01-20T09:00:00Z',
    syllabusFile: 'DBMS_R23.pdf',
    courseOutcomes: [
      { id: 'cs301-co1', code: 'CO1', description: 'Understand database concepts, ER modeling, and relational model.', bloomLevel: 'Understand' },
      { id: 'cs301-co2', code: 'CO2', description: 'Write complex SQL queries for data retrieval and manipulation.', bloomLevel: 'Apply' },
      { id: 'cs301-co3', code: 'CO3', description: 'Apply normalization techniques to design efficient relational schemas.', bloomLevel: 'Apply' },
      { id: 'cs301-co4', code: 'CO4', description: 'Analyze transaction management, concurrency control, and recovery.', bloomLevel: 'Analyze' },
    ],
    units: [
      { id: 'cs301-u1', number: 1, title: 'Introduction to Databases', hours: 9, coMapping: ['CO1'], topics: [
        { id: 'db-t1', title: 'Database Concepts and Architecture' },
        { id: 'db-t2', title: 'Entity-Relationship Model' },
        { id: 'db-t3', title: 'Relational Model' },
        { id: 'db-t4', title: 'Keys and Constraints' },
      ]},
      { id: 'cs301-u2', number: 2, title: 'Structured Query Language', hours: 10, coMapping: ['CO2'], topics: [
        { id: 'db-t5', title: 'DDL Commands: CREATE, ALTER, DROP' },
        { id: 'db-t6', title: 'DML Commands: INSERT, UPDATE, DELETE' },
        { id: 'db-t7', title: 'DQL: SELECT with JOINs and Subqueries' },
        { id: 'db-t8', title: 'Views, Triggers, and Stored Procedures' },
      ]},
      { id: 'cs301-u3', number: 3, title: 'Normalization', hours: 8, coMapping: ['CO3'], topics: [
        { id: 'db-t9', title: 'Functional Dependencies' },
        { id: 'db-t10', title: 'First, Second, and Third Normal Forms' },
        { id: 'db-t11', title: 'Boyce-Codd Normal Form (BCNF)' },
        { id: 'db-t12', title: 'Multivalued Dependencies and 4NF' },
      ]},
      { id: 'cs301-u4', number: 4, title: 'Transaction Management', hours: 10, coMapping: ['CO4'], topics: [
        { id: 'db-t13', title: 'ACID Properties' },
        { id: 'db-t14', title: 'Concurrency Control Protocols' },
        { id: 'db-t15', title: 'Lock-based and Timestamp Protocols' },
        { id: 'db-t16', title: 'Recovery Techniques' },
      ]},
      { id: 'cs301-u5', number: 5, title: 'Advanced Database Systems', hours: 8, coMapping: ['CO1', 'CO4'], topics: [
        { id: 'db-t17', title: 'Distributed Databases' },
        { id: 'db-t18', title: 'NoSQL Databases' },
        { id: 'db-t19', title: 'Data Warehousing and OLAP' },
        { id: 'db-t20', title: 'Database Security' },
      ]},
    ],
    textbooks: [
      { id: 'tb3', title: 'Database System Concepts', author: 'Silberschatz, Korth, Sudarshan', edition: '7th Edition', publisher: 'McGraw-Hill', year: '2020', courseIds: ['cs301'], type: 'textbook' },
    ],
    referenceBooks: [
      { id: 'rb3', title: 'Fundamentals of Database Systems', author: 'Ramez Elmasri, Shamkant Navathe', edition: '7th Edition', publisher: 'Pearson', year: '2017', courseIds: ['cs301'], type: 'reference' },
    ],
    mappings: [
      { courseOutcomeId: 'CO1', mappings: { PO1: 3, PO2: 2, PO3: 2, PO4: 1, PO5: 2, PO6: 1, PSO1: 3, PSO2: 2 } },
      { courseOutcomeId: 'CO2', mappings: { PO1: 3, PO2: 3, PO3: 3, PO4: 2, PO5: 3, PO6: 1, PSO1: 3, PSO2: 3 } },
      { courseOutcomeId: 'CO3', mappings: { PO1: 2, PO2: 3, PO3: 2, PO4: 2, PO5: 2, PO6: 2, PSO1: 2, PSO2: 2 } },
      { courseOutcomeId: 'CO4', mappings: { PO1: 3, PO2: 2, PO3: 3, PO4: 3, PO5: 2, PO6: 2, PSO1: 3, PSO2: 3 } },
    ],
  },
  {
    id: 'cs202',
    name: 'Object Oriented Programming',
    code: 'CS202',
    program: 'B.Tech CSE',
    department: 'Computer Science & Engineering',
    year: 'II Year',
    semester: '3rd Semester',
    regulation: 'R23',
    credits: 3,
    totalHours: 40,
    description: 'Covers object-oriented paradigm using Java/C++: classes, objects, inheritance, polymorphism, encapsulation, and design patterns.',
    prerequisites: ['Programming in C'],
    status: 'indexed',
    uploadedAt: '2024-01-18T09:00:00Z',
    syllabusFile: 'OOP_R23.pdf',
    courseOutcomes: [
      { id: 'cs202-co1', code: 'CO1', description: 'Understand OOP concepts including classes, objects, and encapsulation.', bloomLevel: 'Understand' },
      { id: 'cs202-co2', code: 'CO2', description: 'Apply inheritance and polymorphism to design reusable software.', bloomLevel: 'Apply' },
      { id: 'cs202-co3', code: 'CO3', description: 'Implement exception handling and file I/O mechanisms.', bloomLevel: 'Apply' },
      { id: 'cs202-co4', code: 'CO4', description: 'Design software using standard design patterns.', bloomLevel: 'Create' },
    ],
    units: [
      { id: 'cs202-u1', number: 1, title: 'Classes and Objects', hours: 8, coMapping: ['CO1'], topics: [
        { id: 'oop-t1', title: 'Introduction to OOP' },
        { id: 'oop-t2', title: 'Classes and Objects' },
        { id: 'oop-t3', title: 'Constructors and Destructors' },
      ]},
      { id: 'cs202-u2', number: 2, title: 'Inheritance and Polymorphism', hours: 9, coMapping: ['CO2'], topics: [
        { id: 'oop-t4', title: 'Types of Inheritance' },
        { id: 'oop-t5', title: 'Method Overloading and Overriding' },
        { id: 'oop-t6', title: 'Virtual Functions and Abstract Classes' },
      ]},
      { id: 'cs202-u3', number: 3, title: 'Encapsulation and Abstraction', hours: 7, coMapping: ['CO1'], topics: [
        { id: 'oop-t7', title: 'Access Modifiers' },
        { id: 'oop-t8', title: 'Abstract Classes and Interfaces' },
      ]},
      { id: 'cs202-u4', number: 4, title: 'Exception Handling and I/O', hours: 8, coMapping: ['CO3'], topics: [
        { id: 'oop-t9', title: 'Exception Handling Mechanisms' },
        { id: 'oop-t10', title: 'File I/O Streams' },
      ]},
      { id: 'cs202-u5', number: 5, title: 'Design Patterns', hours: 8, coMapping: ['CO4'], topics: [
        { id: 'oop-t11', title: 'Creational Patterns' },
        { id: 'oop-t12', title: 'Structural Patterns' },
        { id: 'oop-t13', title: 'Behavioral Patterns' },
      ]},
    ],
    textbooks: [
      { id: 'tb4', title: 'Object Oriented Programming with C++', author: 'E. Balagurusamy', edition: '6th Edition', publisher: 'McGraw-Hill', year: '2013', courseIds: ['cs202'], type: 'textbook' },
    ],
    referenceBooks: [
      { id: 'rb4', title: 'The Java Programming Language', author: 'James Gosling', edition: '4th Edition', publisher: 'Addison-Wesley', year: '2005', courseIds: ['cs202'], type: 'reference' },
    ],
    mappings: [
      { courseOutcomeId: 'CO1', mappings: { PO1: 3, PO2: 2, PO3: 2, PO4: 1, PO5: 1, PO6: 1, PSO1: 3, PSO2: 2 } },
      { courseOutcomeId: 'CO2', mappings: { PO1: 3, PO2: 3, PO3: 3, PO4: 2, PO5: 2, PO6: 1, PSO1: 3, PSO2: 3 } },
      { courseOutcomeId: 'CO3', mappings: { PO1: 2, PO2: 2, PO3: 3, PO4: 2, PO5: 2, PO6: 2, PSO1: 2, PSO2: 2 } },
      { courseOutcomeId: 'CO4', mappings: { PO1: 3, PO2: 3, PO3: 3, PO4: 3, PO5: 3, PO6: 2, PSO1: 3, PSO2: 3 } },
    ],
  },
  {
    id: 'cs401',
    name: 'Operating Systems',
    code: 'CS401',
    program: 'B.Tech CSE',
    department: 'Computer Science & Engineering',
    year: 'III Year',
    semester: '5th Semester',
    regulation: 'R23',
    credits: 4,
    totalHours: 45,
    description: 'Principles of modern operating systems including process management, memory management, file systems, and synchronization.',
    prerequisites: ['Computer Organization', 'Data Structures'],
    status: 'indexed',
    uploadedAt: '2024-02-01T09:00:00Z',
    syllabusFile: 'OS_R23.pdf',
    courseOutcomes: [
      { id: 'cs401-co1', code: 'CO1', description: 'Understand OS structure, process states, and scheduling algorithms.', bloomLevel: 'Understand' },
      { id: 'cs401-co2', code: 'CO2', description: 'Analyze deadlock conditions and apply prevention/avoidance strategies.', bloomLevel: 'Analyze' },
      { id: 'cs401-co3', code: 'CO3', description: 'Implement memory management techniques including paging and segmentation.', bloomLevel: 'Apply' },
      { id: 'cs401-co4', code: 'CO4', description: 'Understand file system structures and I/O management.', bloomLevel: 'Understand' },
    ],
    units: [
      { id: 'cs401-u1', number: 1, title: 'Process Management', hours: 9, coMapping: ['CO1'], topics: [
        { id: 'os-t1', title: 'Operating System Overview' },
        { id: 'os-t2', title: 'Process Concept and States' },
        { id: 'os-t3', title: 'CPU Scheduling Algorithms' },
        { id: 'os-t4', title: 'Threads and Multithreading' },
      ]},
      { id: 'cs401-u2', number: 2, title: 'Process Synchronization', hours: 9, coMapping: ['CO2'], topics: [
        { id: 'os-t5', title: 'Critical Section Problem' },
        { id: 'os-t6', title: 'Semaphores and Mutexes' },
        { id: 'os-t7', title: 'Deadlock: Detection, Prevention, Avoidance' },
      ]},
      { id: 'cs401-u3', number: 3, title: 'Memory Management', hours: 9, coMapping: ['CO3'], topics: [
        { id: 'os-t8', title: 'Contiguous Memory Allocation' },
        { id: 'os-t9', title: 'Paging and Segmentation' },
        { id: 'os-t10', title: 'Virtual Memory and Demand Paging' },
        { id: 'os-t11', title: 'Page Replacement Algorithms' },
      ]},
      { id: 'cs401-u4', number: 4, title: 'File System', hours: 9, coMapping: ['CO4'], topics: [
        { id: 'os-t12', title: 'File Concept and Access Methods' },
        { id: 'os-t13', title: 'Directory Structure' },
        { id: 'os-t14', title: 'File System Implementation' },
      ]},
      { id: 'cs401-u5', number: 5, title: 'I/O Systems and Security', hours: 9, coMapping: ['CO4'], topics: [
        { id: 'os-t15', title: 'I/O Hardware and Software' },
        { id: 'os-t16', title: 'Disk Scheduling Algorithms' },
        { id: 'os-t17', title: 'OS Security and Protection' },
      ]},
    ],
    textbooks: [
      { id: 'tb5', title: 'Operating System Concepts', author: 'Silberschatz, Galvin, Gagne', edition: '10th Edition', publisher: 'Wiley', year: '2018', courseIds: ['cs401'], type: 'textbook' },
    ],
    referenceBooks: [
      { id: 'rb5', title: 'Modern Operating Systems', author: 'Andrew S. Tanenbaum', edition: '4th Edition', publisher: 'Pearson', year: '2015', courseIds: ['cs401'], type: 'reference' },
    ],
    mappings: [
      { courseOutcomeId: 'CO1', mappings: { PO1: 3, PO2: 2, PO3: 2, PO4: 1, PO5: 2, PO6: 1, PSO1: 3, PSO2: 2 } },
      { courseOutcomeId: 'CO2', mappings: { PO1: 3, PO2: 3, PO3: 3, PO4: 2, PO5: 2, PO6: 1, PSO1: 2, PSO2: 2 } },
      { courseOutcomeId: 'CO3', mappings: { PO1: 2, PO2: 3, PO3: 3, PO4: 3, PO5: 2, PO6: 2, PSO1: 3, PSO2: 3 } },
      { courseOutcomeId: 'CO4', mappings: { PO1: 3, PO2: 2, PO3: 2, PO4: 2, PO5: 2, PO6: 1, PSO1: 3, PSO2: 2 } },
    ],
  },
  {
    id: 'cs402',
    name: 'Computer Networks',
    code: 'CS402',
    program: 'B.Tech CSE',
    department: 'Computer Science & Engineering',
    year: 'III Year',
    semester: '5th Semester',
    regulation: 'R23',
    credits: 4,
    totalHours: 45,
    description: 'Comprehensive study of computer networking fundamentals, TCP/IP protocol suite, routing, transport layer, and network security.',
    prerequisites: ['Digital Electronics', 'Data Communications'],
    status: 'indexed',
    uploadedAt: '2024-02-05T09:00:00Z',
    syllabusFile: 'CN_R23.pdf',
    courseOutcomes: [
      { id: 'cs402-co1', code: 'CO1', description: 'Understand the OSI and TCP/IP reference models and their layers.', bloomLevel: 'Understand' },
      { id: 'cs402-co2', code: 'CO2', description: 'Apply data link layer protocols and LAN technologies.', bloomLevel: 'Apply' },
      { id: 'cs402-co3', code: 'CO3', description: 'Analyze network layer routing algorithms and IP addressing.', bloomLevel: 'Analyze' },
      { id: 'cs402-co4', code: 'CO4', description: 'Understand transport layer services and application layer protocols.', bloomLevel: 'Understand' },
    ],
    units: [
      { id: 'cs402-u1', number: 1, title: 'Introduction to Networks', hours: 8, coMapping: ['CO1'], topics: [
        { id: 'cn-t1', title: 'Network Fundamentals and Types' },
        { id: 'cn-t2', title: 'OSI Reference Model' },
        { id: 'cn-t3', title: 'TCP/IP Protocol Suite' },
        { id: 'cn-t4', title: 'Transmission Media' },
      ]},
      { id: 'cs402-u2', number: 2, title: 'Data Link Layer', hours: 9, coMapping: ['CO2'], topics: [
        { id: 'cn-t5', title: 'Framing and Error Detection' },
        { id: 'cn-t6', title: 'Flow Control and ARQ Protocols' },
        { id: 'cn-t7', title: 'MAC Protocols and Ethernet' },
        { id: 'cn-t8', title: 'Switching and VLANs' },
      ]},
      { id: 'cs402-u3', number: 3, title: 'Network Layer', hours: 9, coMapping: ['CO3'], topics: [
        { id: 'cn-t9', title: 'IP Addressing and Subnetting' },
        { id: 'cn-t10', title: 'Routing Algorithms: RIP, OSPF, BGP' },
        { id: 'cn-t11', title: 'NAT and ICMP' },
        { id: 'cn-t12', title: 'IPv6' },
      ]},
      { id: 'cs402-u4', number: 4, title: 'Transport Layer', hours: 10, coMapping: ['CO4'], topics: [
        { id: 'cn-t13', title: 'TCP and UDP Services' },
        { id: 'cn-t14', title: 'Congestion Control and Flow Control' },
        { id: 'cn-t15', title: 'Socket Programming' },
      ]},
      { id: 'cs402-u5', number: 5, title: 'Application Layer and Security', hours: 9, coMapping: ['CO4'], topics: [
        { id: 'cn-t16', title: 'DNS, HTTP, SMTP, FTP' },
        { id: 'cn-t17', title: 'Network Security Fundamentals' },
        { id: 'cn-t18', title: 'SSL/TLS and Firewalls' },
      ]},
    ],
    textbooks: [
      { id: 'tb6', title: 'Computer Networks', author: 'Andrew S. Tanenbaum', edition: '5th Edition', publisher: 'Pearson', year: '2011', courseIds: ['cs402'], type: 'textbook' },
    ],
    referenceBooks: [
      { id: 'rb6', title: 'Computer Networking: A Top-Down Approach', author: 'Kurose and Ross', edition: '8th Edition', publisher: 'Pearson', year: '2021', courseIds: ['cs402'], type: 'reference' },
    ],
    mappings: [
      { courseOutcomeId: 'CO1', mappings: { PO1: 3, PO2: 2, PO3: 2, PO4: 1, PO5: 2, PO6: 1, PSO1: 3, PSO2: 2 } },
      { courseOutcomeId: 'CO2', mappings: { PO1: 2, PO2: 3, PO3: 3, PO4: 2, PO5: 3, PO6: 1, PSO1: 2, PSO2: 2 } },
      { courseOutcomeId: 'CO3', mappings: { PO1: 3, PO2: 3, PO3: 3, PO4: 3, PO5: 2, PO6: 2, PSO1: 3, PSO2: 3 } },
      { courseOutcomeId: 'CO4', mappings: { PO1: 3, PO2: 2, PO3: 2, PO4: 2, PO5: 2, PO6: 1, PSO1: 3, PSO2: 2 } },
    ],
  },
];

export const mockTextbooks: Textbook[] = mockCourses.flatMap(c => c.textbooks);
export const mockReferenceBooks: ReferenceBook[] = mockCourses.flatMap(c => c.referenceBooks);

export const mockSyllabusDocuments: SyllabusDocument[] = [
  { id: 'syl1', filename: 'DataStructures_R23.pdf', fileSize: 1245184, uploadedAt: '2024-01-15T09:00:00Z', courseId: 'cs201', status: 'indexed', extractedData: { units: 5, topics: 42, courseOutcomes: 4, textbooks: 3 } },
  { id: 'syl2', filename: 'DBMS_R23.pdf', fileSize: 987654, uploadedAt: '2024-01-20T09:00:00Z', courseId: 'cs301', status: 'indexed', extractedData: { units: 5, topics: 38, courseOutcomes: 4, textbooks: 2 } },
  { id: 'syl3', filename: 'OOP_R23.pdf', fileSize: 876543, uploadedAt: '2024-01-18T09:00:00Z', courseId: 'cs202', status: 'indexed', extractedData: { units: 5, topics: 35, courseOutcomes: 4, textbooks: 2 } },
  { id: 'syl4', filename: 'OS_R23.pdf', fileSize: 1102344, uploadedAt: '2024-02-01T09:00:00Z', courseId: 'cs401', status: 'indexed', extractedData: { units: 5, topics: 40, courseOutcomes: 4, textbooks: 2 } },
  { id: 'syl5', filename: 'CN_R23.pdf', fileSize: 1034567, uploadedAt: '2024-02-05T09:00:00Z', courseId: 'cs402', status: 'indexed', extractedData: { units: 5, topics: 44, courseOutcomes: 4, textbooks: 2 } },
];

export const mockAnalyticsData: AnalyticsData = {
  totalCourses: 48,
  totalDocuments: 52,
  totalTopics: 1284,
  totalCOs: 236,
  unitsProcessed: 240,
  textbooksExtracted: 144,
  coursesByProgram: [
    { program: 'B.Tech CSE', count: 22 },
    { program: 'B.Tech ECE', count: 14 },
    { program: 'B.Tech IT', count: 8 },
    { program: 'MCA', count: 4 },
  ],
  topicsPerCourse: [
    { course: 'Data Structures', topics: 42 },
    { course: 'DBMS', topics: 38 },
    { course: 'OOP', topics: 35 },
    { course: 'Operating Systems', topics: 40 },
    { course: 'Computer Networks', topics: 44 },
  ],
  coDistribution: [
    { level: 'Understand', count: 72 },
    { level: 'Apply', count: 86 },
    { level: 'Analyze', count: 48 },
    { level: 'Evaluate', count: 20 },
    { level: 'Create', count: 10 },
  ],
};

export const mockAIResponses: Record<string, { content: string; citations: { filename: string; unit: string; page: string }[] }> = {
  'What are the topics in Unit 3?': {
    content: `Unit III — Trees contains the following topics:\n\n• Binary Trees — Terminology, properties, and representation\n• Binary Search Trees — Insertion, deletion, and search operations\n• AVL Trees — Balance factor, rotations, insertion and deletion\n• Heap — Min-heap, max-heap, heapify, and heap sort\n• Tree Traversals — Inorder, Preorder, Postorder, Level-order\n• B-Trees and Applications\n\nThis unit is allocated 10 teaching hours and is primarily mapped to CO3 (Apply tree and graph data structures to solve real-world problems).`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'Unit III', page: 'Page 6' }],
  },
  'What is Unit 3 about?': {
    content: `Unit III — Trees (10 hours) covers hierarchical data structures:\n\n• Binary Trees — Terminology, properties, and representation\n• Binary Search Trees — Insertion, deletion, and search operations\n• AVL Trees — Balance factor, rotations, insertion and deletion\n• Heap — Min-heap, max-heap, heapify, and heap sort\n• Tree Traversals — Inorder, Preorder, Postorder, Level-order\n• B-Trees and Applications\n\nMapped to CO3: Apply tree and graph data structures to solve real-world problems.`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'Unit III', page: 'Page 6' }],
  },
  'Show complete syllabus': {
    content: `Data Structures (CS201) — B.Tech CSE, II Year, R23\n\nUnit I — Introduction to Data Structures (8 hrs)\n• Introduction to DS, Abstract Data Types, Arrays, Linked Lists, Applications\n\nUnit II — Stacks and Queues (8 hrs)\n• Stack ADT, Stack Applications, Queue ADT, Circular Queue, Priority Queue, Deque\n\nUnit III — Trees (10 hrs)\n• Binary Trees, BST, AVL Trees, Heap, Tree Traversals, B-Trees\n\nUnit IV — Graphs (8 hrs)\n• Graph Terminology, Graph Representation, BFS, DFS, Shortest Path, MST\n\nUnit V — Sorting and Searching (8 hrs)\n• Bubble Sort, Selection Sort, Insertion Sort, Merge Sort, Quick Sort, Searching Techniques\n\nTotal: 5 Units · 42 Topics · 45 Teaching Hours`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'All Units', page: 'Page 1–30' }],
  },
  'Give me the complete course contents.': {
    content: `Data Structures (CS201) — B.Tech CSE, II Year, R23\n\nUnit I — Introduction to Data Structures (8 hrs)\n• Introduction to DS, Abstract Data Types, Arrays, Linked Lists, Applications\n\nUnit II — Stacks and Queues (8 hrs)\n• Stack ADT, Stack Applications, Queue ADT, Circular Queue, Priority Queue, Deque\n\nUnit III — Trees (10 hrs)\n• Binary Trees, BST, AVL Trees, Heap, Tree Traversals, B-Trees\n\nUnit IV — Graphs (8 hrs)\n• Graph Terminology, Graph Representation, BFS, DFS, Shortest Path, MST\n\nUnit V — Sorting and Searching (8 hrs)\n• Bubble Sort, Selection Sort, Insertion Sort, Merge Sort, Quick Sort, Searching Techniques\n\nTotal: 5 Units · 42 Topics · 45 Teaching Hours`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'All Units', page: 'Page 1–30' }],
  },
  'What textbooks are prescribed?': {
    content: `Prescribed Textbooks for Data Structures (CS201):\n\nTextbooks:\n1. Data Structures Using C — Reema Thareja, 2nd Edition, Oxford University Press (2014)\n2. Data Structures and Algorithm Analysis in C — Mark Allen Weiss, 3rd Edition, Pearson Education (2012)\n\nReference Books:\n1. Introduction to Algorithms — Cormen, Leiserson, Rivest & Stein, 3rd Edition, MIT Press (2009)\n2. Fundamentals of Data Structures in C — Horowitz, Sahni & Anderson-Freed, 2nd Edition, Universities Press (2008)`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'Textbooks Section', page: 'Page 2' }],
  },
  'Show Course Outcomes': {
    content: `Course Outcomes for Data Structures (CS201):\n\nCO1 — Understand fundamental data structure concepts and abstract data types. [Understand]\n\nCO2 — Analyze and implement linear data structures such as stacks and queues. [Apply]\n\nCO3 — Apply tree and graph data structures to solve real-world problems. [Apply]\n\nCO4 — Evaluate and implement searching and sorting techniques with complexity analysis. [Evaluate]`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'Course Outcomes', page: 'Page 3' }],
  },
  'Which CO does Unit 3 support?': {
    content: `Unit III — Trees is mapped to CO3:\n\nCO3: Apply tree and graph data structures to solve real-world problems. (Bloom's Level: Apply)\n\nThis unit directly supports CO3 by covering:\n• Binary Trees and BSTs for efficient data storage and retrieval\n• AVL Trees for self-balancing requirements\n• Heaps for priority-based processing\n• Tree traversal algorithms for systematic data access\n\nUnit IV (Graphs) also maps to CO3, extending the concept to graph-based problems.`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'Unit III', page: 'Page 6' }],
  },
  'Give me a course summary.': {
    content: `Course Summary — Data Structures (CS201)\n\nThis 4-credit course provides a thorough foundation in data structures and algorithm design for B.Tech CSE students in II Year.\n\nKey Highlights:\n• 45 teaching hours across 5 structured units\n• Covers linear structures (arrays, linked lists, stacks, queues) and non-linear structures (trees, graphs)\n• Emphasizes algorithm complexity analysis throughout\n• Includes 5 sorting algorithms and multiple searching techniques\n\nCourse Outcomes: Students will understand data structure concepts (CO1), implement linear structures (CO2), work with trees and graphs (CO3), and analyze sorting/searching algorithms (CO4).\n\nPrerequisites: Programming in C, Problem Solving with Python.`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'Course Overview', page: 'Page 1' }],
  },
  'Give me a summary of this course.': {
    content: `Course Summary — Data Structures (CS201)\n\nThis 4-credit course provides a thorough foundation in data structures and algorithm design for B.Tech CSE students in II Year.\n\nKey Highlights:\n• 45 teaching hours across 5 structured units\n• Covers linear structures (arrays, linked lists, stacks, queues) and non-linear structures (trees, graphs)\n• Emphasizes algorithm complexity analysis throughout\n• Includes 5 sorting algorithms and multiple searching techniques\n\nCourse Outcomes: Students will understand data structure concepts (CO1), implement linear structures (CO2), work with trees and graphs (CO3), and analyze sorting/searching algorithms (CO4).\n\nPrerequisites: Programming in C, Problem Solving with Python.`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'Course Overview', page: 'Page 1' }],
  },
  'Show CO-PO mapping': {
    content: `CO-PO Mapping for Data Structures (CS201):\n\n         PO1  PO2  PO3  PO4  PO5  PO6\nCO1  →    3    2    3    1    2    1\nCO2  →    3    3    2    2    3    1\nCO3  →    2    3    3    2    2    2\nCO4  →    3    2    3    3    2    1\n\nScale: 3 = High  |  2 = Medium  |  1 = Low  |  0 = None\n\nPSO Mapping:\nCO1 → PSO1: 3, PSO2: 2\nCO2 → PSO1: 3, PSO2: 3\nCO3 → PSO1: 2, PSO2: 3\nCO4 → PSO1: 3, PSO2: 2`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'CO-PO Mapping', page: 'Page 4' }],
  },
  'What are the prerequisites?': {
    content: `Prerequisites for Data Structures (CS201):\n\n1. Programming in C — Students must have knowledge of C programming including pointers, structures, and dynamic memory allocation.\n\n2. Problem Solving & Python Programming — Basic algorithmic thinking and programming concepts.\n\nThese prerequisites ensure students can focus on data structure concepts and algorithm implementation without spending time on basic programming syntax.`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'Course Overview', page: 'Page 1' }],
  },
  'Show me Unit 1.': {
    content: `Unit I — Introduction to Data Structures (8 hours)\nMapped to CO1\n\nTopics covered:\n• Introduction to Data Structures — Definition, Classification, Operations\n• Abstract Data Types (ADT) — ADT Concept, List ADT\n• Arrays — One-dimensional, Multi-dimensional arrays, Array operations\n• Linked Lists — Singly, Doubly, Circular Linked Lists\n• Applications of Linked Lists\n\nThis unit establishes the foundational concepts that are built upon throughout the course.`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'Unit I', page: 'Page 5' }],
  },
  'How many units are in this course?': {
    content: `Data Structures (CS201) contains 5 units:\n\nUnit I   — Introduction to Data Structures (8 hrs) → CO1\nUnit II  — Stacks and Queues (8 hrs) → CO2\nUnit III — Trees (10 hrs) → CO3\nUnit IV  — Graphs (8 hrs) → CO3\nUnit V   — Sorting and Searching (8 hrs) → CO4\n\nTotal teaching hours: 45\nTotal topics: 42\nTotal course outcomes: 4`,
    citations: [{ filename: 'DataStructures_R23.pdf', unit: 'Course Structure', page: 'Page 1' }],
  },
};
