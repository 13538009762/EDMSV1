# EDMS User Guide

[English](./user-guide.md) | [简体中文](./user-guide.zh-CN.md)

Welcome to **EDMS (Electronic Document Management System)**. This manual will guide you through all the core features of the system, including AI creation, multi-dimensional knowledge management, real-time collaboration, and approval workflows.

---

## 1. Quick Start

### 1.1 System Initialization (Admin)
When the system is run for the first time or needs a data reset, administrators can log in using the default credentials:
- **Username**: `admin`
- **Password**: `123456`
- **Master Data Import**: Navigate to the "Master Data" page and upload an XLSX template containing Departments, Positions, and Employees information.

### 1.2 Signing In
- **Login Name**: Use the `Login Name` defined in the Master Data to sign in directly.
- **Language Switch**: Click the **Language** button in the top bar to switch between Chinese and English interfaces instantly.

---

## 2. Knowledge Space Management (Multi-Space)
EDMS uses an innovative "Multi-Space" categorization logic, breaking the limits of traditional hierarchical folder structures.

- **Create Space**: In the "Library" section of the sidebar, click the `+` button to create a new Knowledge Space.
- **Multi-Dimensional Association**: A single document can be associated with multiple spaces (Many-to-Many), allowing cross-departmental or cross-project access.
- **Space Views**: You can quickly switch between "Space View" and "Department View" to change how documents are displayed.

---

## 3. Document Editing & Collaboration

### 3.1 Real-time Collaborative Editing
The system integrates Yjs and WebSocket technology to support multi-user simultaneous editing.
- **Real-time Cursors**: In the editor, you can see the cursor positions and editing actions of other online users in real-time.
- **Auto-Save**: All changes are synchronized in real-time and automatically saved to the server. No manual saving is required.

### 3.2 AI Assistant
Boost your productivity with the built-in AI engine:
- **Conversational Generation**: Summon the AI assistant to generate document content via natural language commands (e.g., "Help me write a weekly meeting report framework").
- **Image-to-Doc (OCR)**: Upload images, and the AI will automatically recognize text and convert it into a document format with smart layout.

---

## 4. Version Control & Diff Analysis
- **Version History**: The system automatically records every major edit and generates a version history.
- **Side-by-Side Diff**: In the "History" page, you can select any two versions for comparison. The system will highlight additions (green), deletions (red), or modifications in a **dual-pane view**.

---

## 5. Approval Workflows
The document lifecycle includes: **Draft** $\rightarrow$ **In Approval** $\rightarrow$ **Approved** or **Rejected**.

- **Initiate Approval**: Click "Initiate Approval" in the editor top bar to start the workflow.
- **Inbox**: Approvers can view pending documents in the "Inbox" and provide "Approve" or "Reject" decisions along with comments.
- **Document Locking**: Documents "In Approval" are locked from editing to ensure content integrity during the review process.

---

## 6. Data Security & Traceability

### 6.1 Blockchain Evidence
To ensure core enterprise assets are tamper-proof, the system integrates **Mock Blockchain** technology.
- **Hash Logging**: Once a document is approved, its core hash value is automatically logged as evidence on the blockchain.
- **Verify Evidence**: Users can click the "Blockchain" icon in document details to view traceability info, ensuring content authenticity.

### 6.2 Audit Logs
In the "Audit" tab of document details, you can view all operation records for the document, from creation and edits to permission changes and approvals.

---

## 7. FAQ

- **Why can't I edit a specific document?**
  Please check your permissions (View/Edit/Comment) or see if the document is "In Approval" (locked).
- **How do I batch modify document categories?**
  Select multiple documents in the Library, then click "Move/Categorize" in the batch actions to adjust their associated spaces.
- **How can I recover accidentally deleted content?**
  Go to the "Diff/History" page to view older versions and perform manual recovery if needed.
