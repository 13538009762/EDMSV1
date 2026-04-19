
import os
import sys
import json
import uuid
from flask import Flask

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import db
from app.models import Document, DocumentVersion, User

def create_app():
    app = Flask(__name__)
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "edms.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def _create_tiptap_doc(content: list) -> dict:
    return {"type": "doc", "content": content}

def _create_heading(text: str, level: int = 1) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}]
    }

def _create_paragraph(text: str = "") -> dict:
    item = {"type": "paragraph"}
    if text:
        item["content"] = [{"type": "text", "text": text}]
    return item

def _create_bullet_list(items: list[str]) -> dict:
    return {
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": i}]}]
            } for i in items
        ]
    }

def _create_table(rows_data: list) -> dict:
    """rows_data: List of lists of strings. First list is header."""
    rows = []
    for i, row_cells in enumerate(rows_data):
        cells = []
        for cell_text in row_cells:
            cell_type = "tableHeader" if i == 0 else "tableCell"
            cells.append({
                "type": cell_type,
                "content": [_create_paragraph(cell_text)]
            })
        rows.append({"type": "tableRow", "content": cells})
    return {"type": "table", "content": rows}

def init_all_templates():
    app = create_app()
    with app.app_context():
        print("Starting template initialization with native tables...")
        
        admin = User.query.filter_by(login_name='admin').first() or User.query.first()
        if not admin:
            print("Error: No users found.")
            return

        all_tmpls = {
            "Employment Contract": [
                _create_heading("雇佣合同 (Employment Agreement)"),
                _create_paragraph("甲方（雇主）：[公司全称]"),
                _create_paragraph("乙方（雇员）：[员工姓名]"),
                _create_heading("一、 工作内容", 2),
                _create_paragraph("乙方受雇岗位为 [职位名称]，主要职责如下："),
                _create_bullet_list(["岗位职责 A", "岗位职责 B", "完成上级交办的其他任务"]),
                _create_heading("二、 报酬与福利", 2),
                _create_paragraph("月薪：[金额] 元。发薪日：每月 [日期] 号。")
            ],
            "Meeting Minutes": [
                _create_heading("会议纪要 (Meeting Minutes)"),
                _create_paragraph("时间：2026-XX-XX | 地点：[会议室/线上]"),
                _create_heading("参会人员", 2),
                _create_table([
                    ["姓名", "职务", "签到"],
                    ["[召集人姓名]", "项目经理", "已出席"],
                    ["[记录人姓名]", "行政助理", "已出席"],
                    ["[其他参会人]", "-", "-"]
                ]),
                _create_heading("议题摘要", 2),
                _create_paragraph("1. [详细议题...]"),
                _create_heading("待办任务", 2),
                _create_bullet_list(["任务 1: [负责人] @ [截止日期]"])
            ],
            "Technical Specification": [
                _create_heading("技术规范文档 (Technical Spec)"),
                _create_paragraph("状态：草案 | 密级：内部公开"),
                _create_heading("1. 需求背景", 2),
                _create_paragraph("描述该功能或系统的开发背景。"),
                _create_heading("2. 核心架构表", 2),
                _create_table([
                    ["模块名称", "职责描述", "优先级"],
                    ["数据接口", "负责外部数据读写", "高"],
                    ["协作引擎", "负责实时同步", "高"]
                ])
            ],
            "Weekly Report": [
                _create_heading("工作周报 (Weekly Progress)"),
                _create_paragraph("汇报人：[您的姓名] | 周期：[起始]- [结束]"),
                _create_heading("本周进展统计", 2),
                _create_table([
                    ["任务名称", "完成百分比", "当前状态", "备注"],
                    ["任务 A", "100%", "已交付", "-"],
                    ["任务 B", "60%", "进行中", "待测试"]
                ]),
                _create_heading("下周计划", 2),
                _create_bullet_list(["计划项目 C", "计划项目 D"])
            ],
            "Expense Report": [
                _create_heading("费用报销单 (Expense Report)"),
                _create_paragraph("报销部门：[部门名称] | 申请人：[姓名]"),
                _create_heading("费用明细表", 2),
                _create_table([
                    ["日期", "项目说明", "费用类别", "金额 (元)"],
                    ["2026-04-19", "出差交通费", "差旅费", "150.00"],
                    ["2026-04-19", "客户午餐", "招待费", "200.00"],
                    ["合计", "-", "-", "350.00"]
                ]),
                _create_heading("审批人签章", 2),
                _create_paragraph("部门经理签字：________________")
            ],
            "Simplified Universal Template": [
                _create_heading("简易万能模板 (Simplified Universal Template)"),
                _create_paragraph("标题：[请输入文档标题]"),
                _create_heading("一、 内容描述", 2),
                _create_paragraph("[请在此输入正文...]"),
                _create_heading("二、 核心清单表", 2),
                _create_table([
                    ["序号", "内容项", "备注说明"],
                    ["1", "[输入内容]", "-"],
                    ["2", "[输入内容]", "-"]
                ])
            ]
        }

        for title, elements in all_tmpls.items():
            content = _create_tiptap_doc(elements)
            doc = Document.query.filter_by(title=title, is_template=True).first()
            if not doc:
                doc = Document(
                    owner_id=admin.id,
                    title=title,
                    status="approved",
                    doc_number=f"TMPL-{uuid.uuid4().hex[:6].upper()}",
                    is_template=True,
                    is_public=True
                )
                db.session.add(doc)
                db.session.flush()
            
            print(f"Updating native table content for template: {title}")
            ver = DocumentVersion(
                document_id=doc.id,
                version_no=(doc.current_version.version_no + 1) if doc.current_version else 1,
                content_json=json.dumps(content),
                created_by_id=admin.id
            )
            db.session.add(ver)
            db.session.flush()
            doc.current_version_id = ver.id
        
        db.session.commit()
        print("All templates with native tables initialized successfully!")

if __name__ == "__main__":
    init_all_templates()
