import { Extension, Mark, Node, mergeAttributes } from '@tiptap/core'
export const FontSize = Extension.create({
  name: 'fontSize',
  addOptions() {
    return {
      types: ['textStyle'],
    }
  },
  addGlobalAttributes() {
    return [
      {
        types: this.options.types,
        attributes: {
          fontSize: {
            default: null,
            parseHTML: element => element.style.fontSize?.replace(/['"]+/g, ''),
            renderHTML: attributes => {
              if (!attributes.fontSize) {
                return {}
              }
              return {
                style: `font-size: ${attributes.fontSize}`,
              }
            },
          },
        },
      },
    ]
  },
  addCommands() {
    return {
      setFontSize: (fontSize: string) => ({ chain }: any) => {
        return chain().setMark('textStyle', { fontSize }).run()
      },
      unsetFontSize: () => ({ chain }: any) => {
        return chain().setMark('textStyle', { fontSize: null }).removeEmptyTextStyle().run()
      },
    } as any
  },
})

export const LineHeight = Extension.create({
  name: 'lineHeight',
  addOptions() {
    return {
      types: ['paragraph', 'heading', 'listItem'],
    }
  },
  addGlobalAttributes() {
    return [
      {
        types: this.options.types,
        attributes: {
          lineHeight: {
            default: null,
            parseHTML: element => element.style.lineHeight || null,
            renderHTML: attributes => {
              if (!attributes.lineHeight) {
                return {}
              }
              return {
                style: `line-height: ${attributes.lineHeight}`,
              }
            },
          },
        },
      },
    ]
  },
  addCommands() {
    return {
      setLineHeight: (lineHeight: string) => ({ commands }: any) => {
        let applied = false
        this.options.types.forEach((type: string) => {
          if (commands.updateAttributes(type, { lineHeight })) {
            applied = true
          }
        })
        return applied
      },
      unsetLineHeight: () => ({ commands }: any) => {
        let applied = false
        this.options.types.forEach((type: string) => {
          if (commands.resetAttributes(type, 'lineHeight')) {
            applied = true
          }
        })
        return applied
      },
    } as any
  },
})

export const Indent = Extension.create({
  name: 'indent',
  addOptions() {
    return {
      types: ['paragraph', 'heading'],
      minIndent: 0,
      maxIndent: 8,
    }
  },
  addGlobalAttributes() {
    return [
      {
        types: this.options.types,
        attributes: {
          indent: {
            default: 0,
            parseHTML: element => {
              const padding = element.style.paddingLeft || '0px'
              return parseInt(padding) / 20 || 0
            },
            renderHTML: attributes => {
              if (!attributes.indent) {
                return {}
              }
              return {
                style: `padding-left: ${attributes.indent * 20}px`,
              }
            },
          },
        },
      },
    ]
  },
  addCommands() {
    return {
      indent: () => ({ tr, state, dispatch }: any) => {
        const { selection } = state
        tr.doc.nodesBetween(selection.from, selection.to, (node: any, pos: number) => {
          if (this.options.types.includes(node.type.name)) {
            const indent = (node.attrs.indent || 0) + 1
            if (indent <= this.options.maxIndent) {
              tr.setNodeMarkup(pos, node.type, { ...node.attrs, indent })
            }
          }
        })
        if (dispatch) dispatch(tr)
        return true
      },
      outdent: () => ({ tr, state, dispatch }: any) => {
        const { selection } = state
        tr.doc.nodesBetween(selection.from, selection.to, (node: any, pos: number) => {
          if (this.options.types.includes(node.type.name)) {
            const indent = (node.attrs.indent || 0) - 1
            if (indent >= this.options.minIndent) {
              tr.setNodeMarkup(pos, node.type, { ...node.attrs, indent })
            }
          }
        })
        if (dispatch) dispatch(tr)
        return true
      },
    } as any
  },
})

export const CommentMark = Mark.create({
  name: 'commentMark',

  addAttributes() {
    return {
      commentId: {
        default: null,
        parseHTML: element => element.getAttribute('data-comment-id'),
        renderHTML: attributes => {
          if (!attributes.commentId) {
            return {}
          }
          return {
            'data-comment-id': attributes.commentId,
            class: 'comment-highlight',
            style: 'background-color: rgba(255, 212, 0, 0.4); border-bottom: 2px solid #ffd400;',
          }
        },
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-comment-id]',
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['span', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0]
  },

  addCommands() {
    return {
      setComment: (commentId: string | number) => ({ commands }: any) => {
        return commands.setMark(this.name, { commentId })
      },
      unsetComment: () => ({ commands }: any) => {
        return commands.unsetMark(this.name)
      },
      unsetSpecificComment: (commentId: string | number) => ({ tr, dispatch }: any) => {
        // Advanced: removing specific comments
        return true
      }
    } as any
  },
})
export const TableExit = Extension.create({
  name: 'tableExit',
  addKeyboardShortcuts() {
    return {
      'Enter': () => {
        const { state } = this.editor
        const { $from, empty } = state.selection
        if (!empty) return false
        
        let tableDepth = -1
        for (let d = $from.depth; d > 0; d--) {
          if ($from.node(d).type.name === 'table') {
            tableDepth = d
            break
          }
        }
        if (tableDepth === -1) return false
        const tableEnd = $from.after(tableDepth)
        return this.editor.chain().insertContentAt(tableEnd, { type: 'paragraph' }).focus().run()
      },
    }
  },
})

import { Decoration, DecorationSet } from '@tiptap/pm/view'
import { Plugin, PluginKey } from '@tiptap/pm/state'

export const SearchAndReplace = Extension.create({
  name: 'searchAndReplace',

  addOptions() {
    return {
      searchResultClass: 'search-result',
    }
  },

  addStorage() {
    return {
      searchTerm: '',
      replaceTerm: '',
    }
  },

  addCommands() {
    return {
      setSearchTerm: (term: string) => () => {
        this.storage.searchTerm = term
        return true
      },
      setReplaceTerm: (term: string) => () => {
        this.storage.replaceTerm = term
        return true
      },
      replace: () => ({ editor, state }: any) => {
        const { searchTerm, replaceTerm } = this.storage
        if (!searchTerm) return false
        const { doc } = state
        let foundPos: { from: number, to: number } | null = null
        doc.descendants((node: any, pos: number) => {
          if (foundPos) return false
          if (node.isText) {
            const index = node.text.indexOf(searchTerm)
            if (index !== -1) {
              foundPos = { from: pos + index, to: pos + index + searchTerm.length }
            }
          }
        })
        if (foundPos) {
          editor.chain().insertContentAt(foundPos, replaceTerm).run()
          return true
        }
        return false
      },
      replaceAll: () => ({ editor }: any) => {
        let count = 0
        while (editor.commands.replace() && count < 500) count++
        return count > 0
      },
    } as any
  },

  addProseMirrorPlugins() {
    const extension = this
    return [
      new Plugin({
        key: new PluginKey('searchAndReplace'),
        state: {
          init() { return DecorationSet.empty },
          apply(tr, oldState) {
            const { searchTerm } = extension.storage
            if (!searchTerm || searchTerm.length < 1) return DecorationSet.empty
            const decorations: Decoration[] = []
            tr.doc.descendants((node, pos) => {
              if (node.isText) {
                const text = node.text || ''
                let index = 0
                while ((index = text.indexOf(searchTerm, index)) !== -1) {
                  decorations.push(Decoration.inline(pos + index, pos + index + searchTerm.length, { class: extension.options.searchResultClass }))
                  index += searchTerm.length
                }
              }
            })
            return DecorationSet.create(tr.doc, decorations)
          },
        },
        props: {
          decorations(state) { return this.getState(state) },
        },
      }),
    ]
  },
})
export const PageBreak = Node.create({
  name: 'pageBreak',
  group: 'block',
  
  parseHTML() {
    return [{ tag: 'hr.page-break' }]
  },
  
  renderHTML({ HTMLAttributes }) {
    // 渲染为一个带有 page-break class 的 hr 标签
    return ['hr', mergeAttributes(HTMLAttributes, { class: 'page-break' })]
  },
  
  addCommands() {
    return {
      setPageBreak: () => ({ chain }: any) => {
        // 执行插入命令
        return chain().insertContent({ type: this.name }).run()
      },
    } as any
  },
addKeyboardShortcuts() {
    return {
      'Mod-Enter': () => (this.editor.commands as any).setPageBreak(),
    }
  },
})
