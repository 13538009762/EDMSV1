1. # User Manual: Electronic Document Management System (EDMS)

   ## 1. Introduction

   Welcome to the enterprise Electronic Document Management System (EDMS). This system is designed to help you create, edit, collaboratively review, and approve internal documents in a centralized and transparent environment.

   ## 2. Getting Started

   ### 2.1 Updating Master Data (Administrators Only)

   Before general use, the system administrator must upload the employee and department structures.

   1. Navigate to the **Admin Dashboard** (`/admin`).
   2. Upload the current enterprise reference data in `.XLSX` format.
   3. The system will automatically parse the Excel file, clear old records, and populate the database with updated employees, managers, and departments.

   ### 2.2 System Login

   1. Open the application in your web browser.

   2. Enter your authorized **Login ID (Username)** provided in the enterprise directory.

   3. Click the **Login** button. *(Note: No password is required based on current enterprise configurations).*

   4. You can switch the user interface language (English, Russian, Chinese) using the Locale Switcher located in the top navigation bar.

      ![EN-FIRST](E:\English Encoding\competition\比赛文件\GUIDE\pic\EN-FIRST.png)

   ## 3. Personal Document Storage

   Upon logging in, you will be redirected to the **Dashboard / Personal View**.

   - Here you can view a library of all documents you own.
   - You can easily filter documents by their current statuses: **Draft**, **In Approval**, **Approved**, or **Rejected**.

   ## 4. Working with Documents

   ### 4.1 Creating and Importing

   - **Create:** Click the button to create a new document. A blank canvas will open in the editor.
   - **Import DOCX:** Use the Import view to upload an existing Microsoft Word `.docx` file. Our Python backend will parse the file and preserve its structure and content inside the web editor.

   ### 4.2 Rich Text Editor Features

   The system utilizes a powerful built-in rich text editor (Tiptap). Your changes are saved automatically.

   - **Typography & Style:** Font sizes, bold, italic, underline, and strikethrough.
   - **Structure:** Multi-level headings, bulleted lists, and numbered lists.
   - **Formatting:** Text alignment, line spacing, text color, and background highlighting.
   - **Page Settings:** You can adjust formatting options seamlessly within the editor view.

   ### 4.3 Exporting Documents

   At any time, document owners or users with read access can export the document.

   - Click the **Export** button in the editor.

   - Choose between **PDF** (generated via backend PDF tools) or **DOCX** format.

   - The file will automatically download to your local device.

     ![EN-OPERATE](E:\English Encoding\competition\比赛文件\GUIDE\pic\EN-OPERATE.png)

   ## 5. Collaborative Work & Commenting

   ### 5.1 Sharing Access

   As a document owner, you can share your draft with colleagues to collaborate before the official approval.

   1. Open the document and click **Share**.
   2. A dialog box will appear. Select enterprise users and assign permissions: **View**, **Comment**, or **Edit**.

   ### 5.2 Real-Time Collaboration

   - When multiple users with "Edit" access open the document, the system connects via WebSockets.
   - You will see colored cursors identifying where your colleagues are currently typing.
   - Changes appear on your screen in real-time.

   ### 5.3 Commenting

   1. Highlight any text fragment in the document.

   2. Add a comment explaining your suggestion or question.

   3. Other users can reply to your comment, creating a discussion thread.

   4. The document owner or an authorized editor can mark the comment as **"Completed"** once the issue is resolved.

      ![EN-5](E:\English Encoding\competition\比赛文件\GUIDE\pic\EN-5.png)

   ## 6. The Approval Process

   ### 6.1 Launching an Approval

   When your draft is finalized, you can send it for official approval.

   1. Click **Launch Approval**.

   2. Select the required managers/approvers from the enterprise list.

   3. Choose the Approval Type:

      - **No Strict Order:** All assigned approvers can review and vote at the same time.
      - **Strict Order:** Approvers must review the document sequentially.

   4. The document status will update to **In Approval**.

      ![EN-6-1](E:\English Encoding\competition\比赛文件\GUIDE\pic\EN-6-1.png)

   ### 6.2 Inbox (For Approvers)

   If you are assigned to approve a document, you will find it in your **Inbox View**.

   1. Open the document to review the content and any unresolved comments.

   2. Click **Approve** or **Reject**.

   3. *If Rejecting:* You must enter a reason for refusal. This is saved to the approval history. The document will change to **Rejected** status and editing will be locked.

      ![EN-6-2](E:\English Encoding\competition\比赛文件\GUIDE\pic\EN-6-2.png)

   ## 7. Versioning and Diff Comparison

   If a document is rejected, the owner must create a new version to address the manager's feedback.

   1. The author edits the document, creating a new iteration.

   2. The author re-launches the approval process.

   3. When managers review the updated document, they can open the **Diff View** (Compare Versions).

   4. The system automatically compares the old text with the new text. It visually highlights **added text (green)** and **deleted text (red)**, making it exceptionally easy to verify what changes were made.

   5. Once all approvers accept the changes, the document is marked as **Approved** and becomes part of the permanent corporate library.

      ![EN-7](E:\English Encoding\competition\比赛文件\GUIDE\pic\EN-7.png)

![EN-7-1](E:\English Encoding\competition\比赛文件\GUIDE\pic\EN-7-1.png)