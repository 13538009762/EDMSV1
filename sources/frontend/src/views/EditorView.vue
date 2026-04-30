<template>
  <div class="editor-page" v-loading="loading">
    <div class="header-bar">
      <div class="header-left">
        <el-input v-model="title" style="width: 240px" :disabled="!meta.can_edit" @blur="saveTitle" />
        <el-tag :type="statusTag" class="status-tag">{{ statusLabel }}</el-tag>
        <span class="hint">{{ saveHint }}</span>
        <el-button 
          v-if="meta.status === 'approved' || meta.status === 'ARCHIVED'" 
          type="success" 
          plain 
          size="small"
          :icon="Finished" 
          :loading="isVerifying"
          @click="handleBlockchainVerify"
          style="margin-left: 12px;">
          {{ t('editor.blockchainVerify') }}
        </el-button>
      </div>
      
      <div class="header-right">
        <div class="collab-avatars" v-if="collabColors.length">
          <el-tooltip v-for="(c, i) in collabColors" :key="i" :content="c.name" placement="bottom">
            <div class="avatar-dot" :style="{ backgroundColor: c.color }">{{ c.name.charAt(0).toUpperCase() }}</div>
          </el-tooltip>
        </div>
        
        <div v-if="meta.can_approve" class="approval-shortcuts" style="display: flex; gap: 8px; margin-right: 12px;">
           <el-button type="success" @click="handleEditorApprove">{{ t("inbox.approve") }}</el-button>
           <el-button type="danger" @click="handleEditorReject">{{ t("inbox.reject") }}</el-button>
        </div>

        <el-button 
          v-if="meta.can_edit && meta.doc_type !== 'pdf'"
          :type="isRecording ? 'danger' : 'primary'" 
          plain
          @click="isRecording ? stopRecording() : startRecording()"
          :loading="isProcessingAudio"
        >
          <el-icon style="margin-right: 4px;"><Microphone /></el-icon>
          {{ isRecording ? '停止录音并生成摘要' : '智能会议录音' }}
        </el-button>

        <el-dropdown trigger="click" style="margin-right: 8px;">
          <el-button>{{ t("editor.actions") }} <el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="meta.can_edit" :loading="saving" @click="saveNow">{{ t("editor.save") }}</el-dropdown-item>
              <el-dropdown-item @click="downloadDocx">{{ t("editor.exportDocx") }}</el-dropdown-item>
              <el-dropdown-item @click="downloadPdf">{{ t("editor.exportPdf") }}</el-dropdown-item>
              <el-dropdown-item v-if="meta.can_edit && meta.status === 'draft'" @click="showApproval = true">{{ t("editor.startApproval") }}</el-dropdown-item>
              <el-dropdown-item v-if="meta.status === 'rejected' && isOwner" @click="newVersion">{{ t("editor.newVersion") }}</el-dropdown-item>
              <el-dropdown-item @click="searchVisible = !searchVisible">{{ t("editor.findReplace") }}</el-dropdown-item>
              <el-dropdown-item @click="pageSettingsVisible = true">{{ t("editor.pageSetup") }}</el-dropdown-item>
              <el-dropdown-item v-if="meta.can_manage_permissions && (meta.status === 'draft' || meta.status === 'approved')" @click="showShare = true">{{ t("library.share") }}</el-dropdown-item>
              <el-dropdown-item v-if="(isOwner || isAdmin) && (meta.status === 'draft' || meta.status === 'rejected' || meta.status === 'approved')" divided style="color: var(--el-color-danger)" @click="confirmDeleteDoc">
                {{ t("editor.delete") }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- Rejection Dialog for Editor -->
    <el-dialog v-model="rejectDlg" :title="t('inbox.rejectTitle')" width="420px">
      <div style="margin-bottom: 8px;">{{ t("inbox.reasonPrompt", "Please provide a reason for rejection:") }}</div>
      <el-input v-model="rejectReason" type="textarea" :rows="4" placeholder="..." />
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="rejectDlg = false">{{ t("inbox.cancel") }}</el-button>
          <el-button type="danger" @click="confirmEditorReject">{{ t("inbox.reject") }}</el-button>
        </div>
      </template>
    </el-dialog>

    <div class="editor-toolbar" v-if="editor && meta.doc_type !== 'pdf'" v-show="meta.can_edit">
      <el-button-group class="toolbar-group" style="margin-right: 8px;">
        <el-button size="small" @click="doUndo" :icon="Back" :title="t('editor.toolbar.undo')"></el-button>
        <el-button size="small" @click="doRedo" :icon="Right" :title="t('editor.toolbar.redo')"></el-button>
      </el-button-group>

      <el-select v-model="currentFontFamily" size="small" style="width: 120px" @change="setFontFamily">
        <el-option label="Default" value="Inter, sans-serif" />
        <el-option label="Arial" value="Arial" />
        <el-option label="Courier New" value="Courier New" />
        <el-option label="Georgia" value="Georgia" />
        <el-option label="Times New Roman" value="Times New Roman" />
      </el-select>
      <el-select v-model="currentFontSize" size="small" style="width: 80px" @change="setFontSize">
        <el-option v-for="size in ['12px', '14px', '16px', '18px', '24px', '36px']" :key="size" :label="size" :value="size" />
      </el-select>
      <div class="toolbar-divider"></div>
      
      <el-button-group class="toolbar-group">
        <el-tooltip :content="t('editor.toolbar.bold', 'Bold')" placement="bottom">
          <el-button size="small" :class="{ 'is-active': editor.isActive('bold') }" @click="editor.chain().focus().toggleBold().run()"><b style="font-family: serif">B</b></el-button>
        </el-tooltip>
        <el-tooltip :content="t('editor.toolbar.italic', 'Italic')" placement="bottom">
          <el-button size="small" :class="{ 'is-active': editor.isActive('italic') }" @click="editor.chain().focus().toggleItalic().run()"><i style="font-family: serif">I</i></el-button>
        </el-tooltip>
        <el-tooltip :content="t('editor.toolbar.underline', 'Underline')" placement="bottom">
          <el-button size="small" :class="{ 'is-active': editor.isActive('underline') }" @click="editor.chain().focus().toggleUnderline().run()"><u style="font-family: serif">U</u></el-button>
        </el-tooltip>
        <el-tooltip :content="t('editor.toolbar.strike', 'Strike')" placement="bottom">
          <el-button size="small" :class="{ 'is-active': editor.isActive('strike') }" @click="editor.chain().focus().toggleStrike().run()"><s style="font-family: serif">S</s></el-button>
        </el-tooltip>
      </el-button-group>

      <div class="toolbar-divider"></div>

      <el-button-group class="toolbar-group">
        <el-button size="small" :class="{ 'is-active': editor.isActive('heading', { level: 1 }) }" @click="editor.chain().focus().toggleHeading({ level: 1 }).run()">H1</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive('heading', { level: 2 }) }" @click="editor.chain().focus().toggleHeading({ level: 2 }).run()">H2</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive('heading', { level: 3 }) }" @click="editor.chain().focus().toggleHeading({ level: 3 }).run()">H3</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive('paragraph') }" @click="editor.chain().focus().setParagraph().run()">P</el-button>
      </el-button-group>

      <div class="toolbar-divider"></div>

      <el-button-group class="toolbar-group">
        <el-button size="small" :class="{ 'is-active': editor.isActive({ textAlign: 'left' }) }" @click="editor.chain().focus().setTextAlign('left').run()">L</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive({ textAlign: 'center' }) }" @click="editor.chain().focus().setTextAlign('center').run()">C</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive({ textAlign: 'right' }) }" @click="editor.chain().focus().setTextAlign('right').run()">R</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive({ textAlign: 'justify' }) }" @click="editor.chain().focus().setTextAlign('justify').run()">J</el-button>
      </el-button-group>

      <div class="toolbar-divider"></div>

      <el-button-group class="toolbar-group">
        <el-button size="small" :class="{ 'is-active': editor.isActive('bulletList') }" @click="editor.chain().focus().toggleBulletList().run()">• {{ t("editor.toolbar.bulletList") }}</el-button>
        <el-button size="small" :class="{ 'is-active': editor.isActive('orderedList') }" @click="editor.chain().focus().toggleOrderedList().run()">1. {{ t("editor.toolbar.orderedList") }}</el-button>
      </el-button-group>
      
      <div class="toolbar-divider"></div>
      
      <el-button-group class="toolbar-group">
        <el-button size="small" @click="doOutdent">- {{ t("editor.toolbar.outdent") }}</el-button>
        <el-button size="small" @click="doIndent">+ {{ t("editor.toolbar.indent") }}</el-button>
      </el-button-group>

      <div class="toolbar-divider"></div>
      <el-button size="small" @click="insertImage">{{ t("editor.toolbar.image") }}</el-button>
      <el-button size="small" @click="insertCustomTable">{{ t("editor.toolbar.table") }}</el-button>
      <el-button size="small" type="success" plain @click="importDocx">{{ t("editor.toolbar.importDocx") }}</el-button>
      <el-button size="small" type="info" plain @click="searchVisible = !searchVisible">{{ t("editor.toolbar.findReplace") }}</el-button>
      
      <el-button-group class="toolbar-group" v-if="editor && editor.isActive('table')">
        <el-button size="small" @click="editor.chain().focus().addRowBefore().run()">{{ t("editor.toolbar.addRowBefore") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().addRowAfter().run()">{{ t("editor.toolbar.addRowAfter") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().deleteRow().run()">{{ t("editor.toolbar.deleteRow") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().addColumnBefore().run()">{{ t("editor.toolbar.addColumnBefore") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().addColumnAfter().run()">{{ t("editor.toolbar.addColumnAfter") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().deleteColumn().run()">{{ t("editor.toolbar.deleteColumn") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().deleteTable().run()">{{ t("editor.toolbar.deleteTable") }}</el-button>
        <el-button size="small" @click="editor.chain().focus().toggleHeaderRow().run()">{{ t("editor.toolbar.headerRow") }}</el-button>
      </el-button-group>
      <el-button-group class="toolbar-group" v-if="editor && editor.isActive('image')" style="margin-left: 8px;">
        <el-button size="small" type="warning" plain @click="setImgWidth('100%')">
          {{ t("editor.toolbar.imgSize100") }}
        </el-button>
        <el-button size="small" type="warning" plain @click="setImgWidth('50%')">
          {{ t("editor.toolbar.imgSize50") }}
        </el-button>
        <el-button size="small" type="warning" plain @click="setImgWidth('25%')">
          {{ t("editor.toolbar.imgSize25") }}
        </el-button>
      </el-button-group>

      <div class="toolbar-divider"></div>
      <div style="display: flex; align-items: center; gap: 4px; font-size: 12px; margin-right:8px;">
        <label>{{ t("editor.toolbar.textColor") }}</label>
        <input type="color" v-model="currentColor" @change="setTextColor" style="width: 24px; height: 24px; padding: 0; border: none; cursor: pointer" />
      </div>
      <div style="display: flex; align-items: center; gap: 4px; font-size: 12px">
        <label>{{ t("editor.toolbar.highlight") }}</label>
        <input type="color" v-model="currentHighlight" @change="setHighlight" style="width: 24px; height: 24px; padding: 0; border: none; cursor: pointer" />
      </div>

    </div>

    <!-- Search/Replace Bar -->
    <div v-if="searchVisible" class="search-bar">
      <el-input v-model="searchTerm" :placeholder="t('editor.searchPlaceholder')" size="small" style="width: 150px" @input="updateSearch" />
      <el-input v-model="replaceTerm" :placeholder="t('editor.replacePlaceholder')" size="small" style="width: 150px" />
      <el-button size="small" @click="doReplace">{{ t("editor.replace") }}</el-button>
      <el-button size="small" @click="doReplaceAll">{{ t("editor.replaceAll") }}</el-button>
      <el-button size="small" icon="Close" @click="searchVisible = false" />
    </div>

    <div class="body">
      <div class="main-wrapper">
        <!-- PDF Viewer Mode -->
        <div v-if="meta.doc_type === 'pdf'" class="pdf-view-wrapper">
          <iframe 
            :src="meta.file_path" 
            class="pdf-frame" 
            frameborder="0"
          ></iframe>
        </div>

        <!-- Rich Text Editor Mode -->
        <div 
          v-else-if="editor" 
          class="main-paper" 
          :class="page.paperFormat"
        >
          <div class="watermark-overlay" :style="{ backgroundImage: watermarkDataUrl ? `url(${watermarkDataUrl})` : '' }"></div>
          
          <bubble-menu
            v-if="editor"
            v-show="meta.can_edit"
            :editor="editor"
            :tippy-options="{ duration: 100, placement: 'top' }"
            class="ai-bubble-menu"
          >
            <el-dropdown size="small" @command="handleAiAction" trigger="click" placement="top">
              <el-button size="small" type="primary" plain class="ai-btn">✨ {{ t("editor.ai.assistant") }} <el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="summarize">{{ t("editor.ai.summarize") }}</el-dropdown-item>
                  <el-dropdown-item command="expand">{{ t("editor.ai.expand") }}</el-dropdown-item>
                  <el-dropdown-item command="polish">{{ t("editor.ai.polish") }}</el-dropdown-item>
                  <el-dropdown-item divided command="fix_punctuation">✨ {{ t("editor.ai.fixPunc") }}</el-dropdown-item>
                  <el-dropdown-item divided command="translate_en">{{ t("editor.ai.translateEn") }}</el-dropdown-item>
                  <el-dropdown-item command="translate_zh">{{ t("editor.ai.translateZh") }}</el-dropdown-item>
                  <el-dropdown-item command="translate_ru">{{ t("editor.ai.translateRu") }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </bubble-menu>

          <editor-content :editor="editor" class="tiptap" :style="{ paddingTop: page.marginTop + 'px', paddingBottom: page.marginBottom + 'px' }" />
        </div>
      </div>
      <div class="side">
        <el-tabs v-model="activeSideTab" stretch>
          <!-- AI Tab -->
          <el-tab-pane name="ai">
            <template #label>
              <span>✨ {{ t("editor.ai.aiTab") }}</span>
            </template>
            <div class="ai-panel">
              <!-- AI Tags Section -->
              <div class="ai-tags-section">
                <div class="section-title">
                   <span>🏷️ {{ t("editor.ai.aiTags") }}</span>
                   <el-button link type="primary" size="small" @click="runAutoTag" :loading="tagging">
                     {{ t("editor.ai.aiActionAutoTag") }}
                   </el-button>
                </div>
                <div class="tags-container">
                  <el-tag v-for="tag in aiTags" :key="tag" size="small" round effect="plain" class="ai-tag">
                    {{ tag }}
                  </el-tag>
                  <div v-if="aiTags.length === 0 && !tagging" class="empty-tags">
                    {{ t("editor.ai.noTagsYet") }}
                  </div>
                </div>
              </div>

              <!-- AI Chat Section -->
              <div class="ai-chat-container">
                <transition-group name="msg" tag="div" class="chat-messages" ref="chatScroll">
                  <template v-for="(msg, idx) in aiStore.editorMessages" :key="idx">
                    <div v-if="!msg.hidden" :class="['chat-msg', msg.role]">
                    <div class="msg-content" v-html="renderMarkdown(msg.content)"></div>
                    
                    <div v-if="msg.role === 'ai' || msg.role === 'assistant'" class="msg-footer" style="margin-top: 8px;">
                      <el-button 
                        size="small" 
                        type="primary" 
                        plain 
                        icon="MagicStick" 
                        :disabled="!meta.can_edit"
                        @click="insertChatToEditor(msg.content)"
                      >
                        ✨ {{ t('editor.ai.insertToDoc') }}
                      </el-button>
                    </div>
                    
                    <!-- AI Action Card -->
                    <div v-if="msg.action" class="ai-action-card">
                      <div class="card-header">
                        <el-icon><MagicStick /></el-icon>
                        <span>{{ t('editor.ai.actionConfirmTitle') }}</span>
                      </div>
                      <div class="card-body">
                        <div class="action-desc">
                          {{ msg.action.confirm_prompt || (msg.action.params?.approver_names 
                            ? `立即发起审批：${msg.action.params.approver_names}？` 
                            : t('editor.ai.actionStartApproval', { names: (msg.action.params?.approvers || []).join(', ') })) }}
                        </div>
                      </div>
                      <div class="card-actions">
                        <el-button type="primary" size="small" :disabled="!meta.can_edit" @click="confirmAiAction(msg.action, idx)">
                          {{ t('editor.ai.actionConfirmBtn') }}
                        </el-button>
                        <el-button size="small" @click="msg.action = null">
                          {{ t('editor.ai.actionCancelBtn') }}
                        </el-button>
                      </div>
                    </div>
                    </div>
                  </template>
                  <div v-if="asking" key="typing" class="chat-msg ai typing">
                    <div class="typing-indicator">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                </transition-group>
                  <div v-if="aiStore.editorMessages.length === 0" class="chat-placeholder">
                    <el-empty :description="t('editor.ai.aiChatEmpty')" :image-size="40" />
                  </div>
                
                <div class="chat-input-area">
                  <el-input
                    v-model="aiQuery"
                    type="textarea"
                    :rows="2"
                    :placeholder="t('editor.ai.aiChatPlaceholder')"
                    @keyup.enter.prevent="() => askAi()"
                    resize="none"
                  />
                  <div class="chat-actions">
                    <el-button type="primary" size="small" @click="() => askAi()">
                      {{ t("common.send") }}
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane :label="t('editor.commentsTab')" name="comments">
            <div class="comments-header">
              <el-button v-if="meta.can_comment" size="small" type="primary" style="width: 100%; margin-top: 8px; margin-bottom: 12px;" @click="addCommentOnSelection">
                {{ t("editor.commentSelection") }}
              </el-button>
            </div>
            
            <div class="comment-filters">
              <el-select v-model="filterAuthor" size="small" :placeholder="t('editor.commentsFilters.author')" clearable class="filter-item">
                <el-option v-for="a in authorOptions" :key="a" :label="a" :value="a" />
              </el-select>
              <el-select v-model="filterStatus" size="small" :placeholder="t('editor.commentsFilters.status')" class="filter-item">
                <el-option :label="t('editor.commentsFilters.all')" value="all" />
                <el-option :label="t('editor.commentsFilters.active')" value="active" />
                <el-option :label="t('editor.commentsFilters.resolved')" value="resolved" />
              </el-select>
              <el-date-picker v-model="filterDate" type="date" :placeholder="t('editor.commentsFilters.date')" size="small" class="filter-item" value-format="YYYY-MM-DD" style="width:100%" />
            </div>

            <div class="comments-list">
              <div v-for="m in threadedComments" :key="m.id" class="comment-group">
                <div class="comment" :class="{ 'resolved': m.status === 'resolved' }" @click="scrollToComment(m.id)">
                  <div class="meta">
                    <div style="font-weight: 500;">{{ m.author_login }}</div>
                    <div class="meta-right">
                      <span>{{ formatLocalDate(m.created_at) }} · {{ m.status }}</span>
                      <el-button
                        v-if="m.status === 'active'"
                        link
                        type="primary"
                        @click.stop="resolveComment(m.id)"
                        size="small"
                      >
                        {{ t("editor.resolve") }}
                      </el-button>
                    </div>
                  </div>
                  <div class="comment-body">{{ m.body }}</div>
                  <el-input
                    v-model="replyMap[m.id]"
                    :placeholder="t('editor.replyPlaceholder')"
                    size="small"
                    @keyup.enter="replyTo(m.id)"
                    @click.stop
                  />
                </div>
                
                <div v-if="m.replies && m.replies.length" class="replies">
                  <div v-for="r in m.replies" :key="r.id" class="comment reply" :class="{ 'resolved': r.status === 'resolved' }">
                    <div class="meta">
                      <div style="font-weight: 500;">{{ r.author_login }}</div>
                      <div class="meta-right">
                        <span>{{ formatLocalDate(r.created_at) }}</span>
                      </div>
                    </div>
                    <div class="comment-body">{{ r.body }}</div>
                  </div>
                </div>
              </div>
              <el-empty v-if="threadedComments.length === 0" :description="t('editor.commentsFilters.noComments')" :image-size="60" />
            </div>
            <el-button size="small" @click="loadComments" style="width:100%; margin-top: 12px;">{{ t("editor.refreshComments") }}</el-button>
          </el-tab-pane>

          <el-tab-pane :label="t('editor.versionsTab')" name="versions">
            <div class="version-list-container">
              <div class="version-header">
                <el-button size="small" type="primary" @click="$router.push(`/doc/${docId}/diff`)">{{ t("editor.viewDiff") }}</el-button>
                <el-button size="small" @click="loadVersions">{{ t("editor.refresh") }}</el-button>
              </div>
              <div class="version-items">
                <div v-for="v in versionList" :key="v.id" class="version-item">
                  <div class="v-meta">
                    <span class="v-no">V{{ v.version_no }}</span>
                    <span class="v-user">{{ v.created_by_name }}</span>
                  </div>
                  <div class="v-time">{{ formatLocalDate(v.created_at) }}</div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <DocumentShareDialog v-model="showShare" :document-id="docId" @saved="loadDoc" />

    <el-dialog v-model="pageSettingsVisible" :title="t('editor.pageSetupTitle')" width="400px">
      <el-form label-width="120px">
        <el-form-item :label="t('editor.orientation')">
          <el-radio-group v-model="page.orientation">
            <el-radio label="portrait" value="portrait">{{ t("editor.portrait") }}</el-radio>
            <el-radio label="landscape" value="landscape">{{ t("editor.landscape") }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('editor.paperSize')">
          <el-select v-model="page.paperFormat">
            <el-option label="A4" value="A4" />
            <el-option label="Letter" value="Letter" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('editor.marginTop')">
          <el-slider v-model="page.marginTop" :min="0" :max="100" />
        </el-form-item>
        <el-form-item :label="t('editor.marginBottom')">
          <el-slider v-model="page.marginBottom" :min="0" :max="100" />
        </el-form-item>
        <el-form-item :label="t('editor.showPageNumber')">
          <el-switch v-model="page.showPageNumber" />
        </el-form-item>
        <el-form-item :label="t('library.wikiTree')">
          <el-select v-model="selectedSpaceId" style="width: 100%">
            <el-option :label="t('library.scopeMine')" value="none" />
            <el-option v-for="s in spacesOptions" :key="s.id" :label="t('space.' + s.name, s.name)" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="savePageSettings">{{ t("editor.apply") }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showApproval" :title="t('editor.approvalTitle')" width="420px" destroy-on-close>
      <el-radio-group v-model="approvalType">
        <el-radio label="parallel" value="parallel">{{ t("editor.parallel") }}</el-radio>
        <el-radio label="sequential" value="sequential">{{ t("editor.sequential") }}</el-radio>
      </el-radio-group>
      <div style="margin-top: 12px; display: flex; gap: 8px;">
        <el-select v-model="selectedDeptId" clearable :placeholder="t('profile.dept')" style="width: 150px">
          <el-option v-for="d in deptOptions" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
        <el-select
          v-model="approverIds"
          multiple
          filterable
          :placeholder="t('editor.approversPlaceholder')"
          style="flex: 1"
        >
          <el-option v-for="u in filteredUserOptions" :key="u.id" :label="`${u.display_name || u.login_name}`" :value="u.id" />
        </el-select>
      </div>
      <template #footer>
        <el-button type="primary" :loading="loading" :disabled="loading" @click="startApproval">{{ t("editor.start") }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import * as Y from "yjs";
import { Awareness } from "y-protocols/awareness";
import { useEditor, EditorContent, BubbleMenu } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Collaboration from "@tiptap/extension-collaboration";
import CollaborationCursor from "@tiptap/extension-collaboration-cursor";
import Underline from "@tiptap/extension-underline";
import TextAlign from "@tiptap/extension-text-align";
import TextStyle from "@tiptap/extension-text-style";
import Color from "@tiptap/extension-color";
import Highlight from "@tiptap/extension-highlight";
import FontFamily from "@tiptap/extension-font-family";
import Image from "@tiptap/extension-image";

import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import { ArrowDown, Back, Right, MagicStick, Microphone, Finished } from "@element-plus/icons-vue";

import { FontSize, LineHeight, Indent, CommentMark, TableExit, SearchAndReplace } from "@/utils/tiptapExtensions";
import api from "@/api/client";
import { useAuthStore } from "@/stores/auth";
import { useAiStore } from "@/stores/ai";
import { attachDocCollab } from "@/composables/useDocSocket";

import { ElMessage, ElMessageBox, ElNotification, ElLoading } from "element-plus";
import { marked } from 'marked';
import mammoth from "mammoth";
import { Markdown } from "tiptap-markdown";
import DocumentShareDialog from "@/components/DocumentShareDialog.vue";
import { formatLocalDate } from "@/utils/date";

const CustomImage = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      width: {
        default: null,
        parseHTML: element => element.getAttribute('width'),
        renderHTML: attributes => {
          if (!attributes.width) return {};
          return { width: attributes.width };
        }
      }
    };
  }
}).configure({ allowBase64: true });
const route = useRoute();
const router = useRouter();
const { t, locale } = useI18n();
const auth = useAuthStore();
const docId = computed(() => Number(route.params.id));
const isAdmin = computed(() => auth.user?.login_name === 'admin');
const isOwner = computed(() => auth.user?.id === meta.value.owner_id);

const loading = ref(true);
const saving = ref(false);
const title = ref("");
const meta = ref<any>({
  status: "draft",
  can_edit: false,
  can_comment: false,
  can_manage_permissions: false,
  owner_id: 0,
  doc_type: "rich_text",
  file_path: null,
});

const statusTag = computed(() => {
  const map: any = { draft: 'info', approved: 'success', rejected: 'danger', pending: 'warning', ARCHIVED: 'info' };
  return map[meta.value.status] || 'info';
});
const statusLabel = computed(() => {
  return t(`editor.status.${meta.value.status}`) || meta.value.status;
});

const isVerifying = ref(false);

const handleBlockchainVerify = async () => {
  isVerifying.value = true;
  try {
    const res = await api.get(`/documents/${docId.value}/verify`);
    
    if (res.data.safe) {
      ElNotification({
        title: t('editor.blockchainPassed'),
        message: `
          <div style="margin-top: 5px;">
            <p style="color: #67C23A; font-weight: bold; margin-bottom: 8px; display:flex; align-items:center; gap:4px">
              <span style="font-size: 16px;">✔</span> ${t('editor.blockchainVerified')}
            </p>
            <div style="padding: 8px; background: rgba(0,0,0,0.03); border-radius: 4px;">
              <p style="font-size: 12px; color: #909399; margin: 0; word-break: break-all;">
                <b>${t('editor.blockchainTxHash')}:</b><br/>${res.data.tx_hash}
              </p>
            </div>
          </div>
        `,
        dangerouslyUseHTMLString: true,
        type: 'success',
        duration: 5000
      });
    } else {
      ElNotification({
        title: t('editor.blockchainTamperAlert'),
        message: `
          <div style="margin-top: 5px;">
            <p style="color: #F56C6C; font-weight: bold; margin-bottom: 8px; display:flex; align-items:center; gap:4px">
              <span style="font-size: 16px;">❌</span> ${res.data.msg}
            </p>
            <p style="font-size: 12px; color: #606266; margin: 0;">${t('editor.blockchainInterceptionMsg')}</p>
          </div>
        `,
        dangerouslyUseHTMLString: true,
        type: 'error',
        duration: 0 
      });
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || "验证请求失败");
  } finally {
    isVerifying.value = false;
  }
};

const showShare = ref(false);
const comments = ref<Array<any>>([]);
const replyMap = ref<Record<number, string>>({});
const activeSideTab = ref("ai");
const aiTags = ref<string[]>([]);
const tagging = ref(false);
const aiQuery = ref("");

// --- Meeting Recording Logic ---
const isRecording = ref(false);
const isProcessingAudio = ref(false);
let mediaRecorder: MediaRecorder | null = null;
let audioChunks: Blob[] = [];

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      await handleAudioUpload(audioBlob);
    };

    mediaRecorder.start();
    isRecording.value = true;
    ElMessage.info("会议录音开始...");
  } catch (err) {
    console.error("麦克风授权失败", err);
    ElMessage.error("获取麦克风权限失败，请检查设置。");
  }
};

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    isRecording.value = false;
  }
};

const handleAudioUpload = async (blob: Blob) => {
  isProcessingAudio.value = true;
  const loadingInstance = ElLoading.service({ text: 'AI 正在转写并生成会议摘要...', background: 'rgba(0, 0, 0, 0.7)' });
  try {
    const formData = new FormData();
    formData.append('audio', blob, 'meeting.webm');
    const { data } = await api.post('/api/ai/meeting-summary', formData);
    
    if (data.code === 200) {
      const summaryHtml = marked.parse(data.data.summary_markdown);
      editor.value?.commands.insertContent(summaryHtml);
      ElMessage.success("会议摘要已插入文档");
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || "音频处理失败");
  } finally {
    isProcessingAudio.value = false;
    loadingInstance.close();
  }
};
const askingCount = ref(0);
const asking = computed(() => askingCount.value > 0);
const aiStore = useAiStore();
const chatScroll = ref<HTMLElement | null>(null);

const scrollToBottom = async (force = false) => {
  await nextTick();
  if (chatScroll.value) {
    const el = (chatScroll.value as any).$el || chatScroll.value;
    const isAtTop = el.scrollTop === 0;
    const isNearBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 300;
    
    if (force || isNearBottom || (el.scrollHeight > el.clientHeight && isAtTop)) {
      el.scrollTop = el.scrollHeight;
    }
  }
};

const spacesOptions = ref<Array<{ id: any, name: string }>>([]);
const selectedSpaceId = ref<any>(null);

// ==========================================
// AI Core Helper Functions (Unified)
// ==========================================

const renderMarkdown = (text: string) => {
  if (!text) return '';
  const cleanText = text.replace(/\[ACTION:[\s\S]*?\]/g, '').trim();
  return marked.parse(cleanText);
};

const insertChatToEditor = (content: string) => {
  if (!editor.value || !content) return;
  
  // Clean content: remove [ACTION:...] and JSON blocks
  let cleanContent = content.replace(/\[ACTION:[\s\S]*?\]/g, '')
                            .replace(/```json[\s\S]*?```/g, "")
                            .trim();
  
  const html = renderMarkdown(cleanContent);
  editor.value?.commands.insertContent(html);
  ElMessage.success(t("editor.ai.insertSuccess"));
};

const confirmAiAction = async (action: any, idx: number) => {
  if (!action) return;
  const type = String(action.action || '').toUpperCase();
  if (action.action === "start_approval" || type === "START_APPROVAL") {
    const p = action.params || action;
    const approvers = p.approvers || [];
    
    // 💡 如果已经有具体的 ID，直接发起审批，不再弹窗
    if (approvers.length > 0 && typeof approvers[0] === 'number') {
      try {
        loading.value = true;
        await api.post(`/documents/${docId.value}/approvals`, {
          type: p.type || p.approval_type || "sequential",
          approvers: approvers,
        });
        ElMessage.success(t("editor.messages.sentToApproval") || "已成功发起审批");
        aiStore.editorMessages[idx].action = null;
        loadDoc(true);
        return;
      } catch (err) {
        ElMessage.error(t("common.failed"));
      } finally {
        loading.value = false;
      }
    } else {
      // 💡 如果只有姓名没有 ID，则回退到弹窗让用户手动选
      window.dispatchEvent(new CustomEvent('edms:trigger_approval', { 
        detail: { 
          approvers: approvers, 
          type: p.type || 'parallel'
        } 
      }));
    }
  } else if (action.action === "recall_approval" || type === "RECALL_APPROVAL") {
    try {
      loading.value = true;
      await api.post(`/approvals/recall`, { doc_id: action.params?.doc_id || docId.value });
      ElMessage.success("审批申请已成功撤回");
      aiStore.editorMessages[idx].action = null;
      loadDoc(true);
    } catch (err: any) {
      ElMessage.error(err.response?.data?.error || "撤回失败");
    } finally {
      loading.value = false;
    }
  } else if (['QUERY', 'SEARCH', 'STATS', 'DASHBOARD', 'GET', 'LIST', 'COUNT', 'VIEW', 'SHOW', 'READ'].some(k => type.includes(k))) {
     // 💡 Handle any variation of query/search/stats/dashboard/get/list
     const p = action.params || {};
     let resultHtml = "";
     try {
       if (type.includes('DATA') || type.includes('SEARCH') || type.includes('GET') || type.includes('LIST')) {
         const entity = (p.ENTITY || p.entity || '').toLowerCase();
         const q = p.QUERY || p.query || 'all';
         const res = await api.get(entity.includes('approval') ? '/approvals/inbox' : (entity.includes('user') ? '/users' : '/documents'), { params: { search: q } });
         resultHtml = JSON.stringify(res.data.items || res.data);
       } else if (type.includes('STATS') || type.includes('COUNT')) {
         const sType = (p.TYPE || p.type || '').toLowerCase();
         const res = await api.get(sType.includes('user') ? '/users/stats' : '/documents/stats');
         resultHtml = `📊 统计: ${res.data.total_count}`;
       } else if (type.includes('DASHBOARD')) {
         const res = await api.get('/dashboard/stats');
         resultHtml = JSON.stringify(res.data);
       }
       if (resultHtml) {
         aiStore.addMessage('editor', 'user', `[反馈]:\n${resultHtml}`, null, true);
         askAi(true);
       }
     } catch (e) {
       console.error("Action execution failed", e);
     }
  }
  aiStore.editorMessages[idx].action = null;
};

async function runAutoTag() {
  if (!editor.value) return;
  tagging.value = true;
  try {
    const text = editor.value.getText().slice(0, 500);
    const response = await api.post("/ai/generate", { action: "auto_tag", prompt: text, lang: locale.value });
    if (response.data?.content) {
      aiTags.value = response.data.content.split(",").map((s: string) => s.trim());
    }
  } catch (err) {
    console.error("Auto-tag failed:", err);
  } finally {
    tagging.value = false;
  }
}

async function askAi(isFeedback = false) {
  if (!isFeedback && (!aiQuery.value.trim() || asking.value || !editor.value)) return;
  
  const query = aiQuery.value.trim();
  if (!isFeedback) {
    aiStore.addMessage('editor', 'user', query);
    aiQuery.value = "";
  }
  askingCount.value++;
  scrollToBottom(true); // 💡 Force scroll on send
  
  // Scoped RAG: Send document metadata + context + user question
  const docMeta = {
    id: route.params.id,
    title: meta.value?.title || "未命名文档",
    status: meta.value?.status || "draft"
  };
  const docContext = `[当前编辑文档信息] ID: ${docMeta.id}, 标题: ${docMeta.title}, 状态: ${docMeta.status}\n\n内容摘要: ${editor.value?.getText().slice(0, 4000) || ""}`;
  
  try {
     const response = await fetch('/api/ai/chat', {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${auth.token}` },
      body: JSON.stringify({ 
        messages: aiStore.editorMessages.filter(m => m.content && m.content.trim() !== '').slice(-15), 
        context_url: route.path,
        doc_context: docContext 
      })
    });
    
    if (!response.ok) throw new Error("AI request failed");
    
    const aiMsg: any = { role: 'ai', content: "", action: undefined };
    aiStore.editorMessages.push(aiMsg);
    
    const reader = response.body?.getReader();
    if (!reader) return;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = new TextDecoder().decode(value);
      const lines = chunk.split("\n");
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const raw = line.slice(6).trim();
          if (raw === "[DONE]") break;
          try {
            const data = JSON.parse(raw);
            if (data.content) {
              aiMsg.content += data.content;
            } else if (data.type === "done") {
              // 1. Handle QUERY_DATA Tag (Search Logic)
              const queryDataRegex = /\[ACTION:\s*QUERY_DATA,\s*ENTITY:\s*([a-z]+),\s*QUERY:\s*([^\]]+)\]/i;
              const qMatch = aiMsg.content.match(queryDataRegex);
              if (qMatch) {
                const entity = qMatch[1];
                const query = qMatch[2];
                aiMsg.content = aiMsg.content.replace(queryDataRegex, '').trim();
                const tempMsg = aiMsg.content;
                aiMsg.content = tempMsg + "\n\n⌛ *正在检索 " + entity + "...*"; 
                try {
                  let res;
                  let resultHtml = "";
                  if (entity === 'documents') {
                    res = await api.get('/documents', { params: { search: query } });
                    const items = res.data.items || [];
                    if (items.length > 0) {
                      resultHtml = "\n\n### 找到以下文档:\n" + items.map((d:any) => `- **[${d.doc_number}] ${d.title}** (ID: ${d.id}, 状态: ${d.status})`).join('\n');
                    } else {
                      resultHtml = "\n\n❌ 未找到相关文档。";
                    }
                  } else if (entity === 'users') {
                    res = await api.get('/users', { params: { search: query } });
                    const items = (res.data.items || []).filter((u: any) => u.id !== auth.user?.id);
                    if (items.length > 1) {
                      resultHtml = "\n\n### 找到以下用户（请告知确认发给哪位）:\n" + items.map((u:any) => `- **${u.display_name}** (${u.login_name}) - ${u.department_name}`).join('\n');
                    } else if (items.length === 1) {
                      const foundUser = items[0];
                      const docIdStr = route.params.id;
                      resultHtml = `\n\n✅ 已定位到用户: **${foundUser.display_name}**`;
                      
                      aiMsg.action = {
                        action: 'start_approval',
                        confirm_prompt: `立即发起审批：${foundUser.display_name}？`,
                        params: {
                          doc_id: docIdStr ? Number(docIdStr) : null,
                          approvers: [foundUser.id],
                          approver_names: foundUser.display_name,
                          type: 'sequential'
                        }
                      };

                      console.log("[DEBUG] EditorView Auto-triggering approval dialog for:", foundUser.display_name);
                      window.dispatchEvent(new CustomEvent('edms:trigger_approval', { 
                        detail: { approvers: [foundUser.id], type: 'sequential' } 
                      }));
                    } else if (entity === 'approvals') {
                      res = await api.get('/approvals/inbox');
                      const items = res.data.items || [];
                      if (items.length > 0) {
                        resultHtml = "\n\n### 待处理审批:\n" + items.map((a:any) => `- **${a.title}** (来自: ${a.initiator_name}, 进度: ${a.progress.done}/${a.progress.total})`).join('\n');
                      } else {
                        resultHtml = "\n\n✅ 暂无待处理审批。";
                      }
                    }
                  } else {
                    // Handle QUERY_STATS and QUERY_DASHBOARD (Legacy/General tags)
                    const statsMatch = aiMsg.content.match(/\[ACTION:\s*QUERY_STATS,\s*TYPE:\s*([a-zA-Z0-9_-]+)\]/i);
                    const dashMatch = aiMsg.content.match(/\[ACTION:\s*QUERY_DASHBOARD,\s*TYPE:\s*([a-z]+)\]/i);
                    
                    if (statsMatch) {
                      const type = statsMatch[1];
                      aiMsg.content = aiMsg.content.replace(/\[ACTION:\s*QUERY_STATS,\s*TYPE:\s*([a-zA-Z0-9_-]+)\]/i, '').trim();
                      const res = await api.get(type === 'user_count' ? '/users/stats' : '/documents/stats');
                      resultHtml = `📊 **系统统计**: ${type === 'user_count' ? '总成员' : '可见文档'}共 **${res.data.total_count}**。`;
                    } else if (dashMatch) {
                      const dType = dashMatch[1];
                      aiMsg.content = aiMsg.content.replace(/\[ACTION:\s*QUERY_DASHBOARD,\s*TYPE:\s*([a-z]+)\]/i, '').trim();
                      const res = await api.get('/dashboard/stats');
                      const data = res.data;
                      if (dType === 'storage') resultHtml = `📊 存储占用: **${data.storage_info.total_size_mb} MB**`;
                      else if (dType === 'security') resultHtml = `🛡️ 安全监控: 已上链 **${data.blockchain_stats.on_chain_count}** 份`;
                      else resultHtml = `📑 总览: 成员 ${data.total_users}, 文档 ${data.total_docs}`;
                    }
                  }
                  if (resultHtml !== undefined) {
                    aiMsg.content = tempMsg + (resultHtml || "");
                    
                    // 💡 Feed back to AI
                    if (resultHtml) {
                      aiStore.addMessage('editor', 'user', `[系统反馈]:\n${resultHtml}`, null, true);
                      askAi(true);
                    }
                  }
                } catch (e) {
                  aiMsg.content = tempMsg + "\n\n⚠️ 查询失败。";
                }
              }

              // 2. Handle start_approval Tag/JSON
              const approvalRegex = /\[ACTION:\s*start_approval,\s*PARAMS:\s*(\{[\s\S]*?\})\]/i;
              const aMatch = aiMsg.content.match(approvalRegex);
              const jsonMatch = aiMsg.content.match(/```json\s*(\{[\s\S]*?\})\s*```/);
              
              if ((aMatch || jsonMatch) && !aiMsg.action) {
                try {
                  let rawAction = aMatch ? aMatch[1] : jsonMatch![1];
                  let actionData = JSON.parse(rawAction);
                  
                  if (actionData.start_approval && !actionData.action) {
                    actionData = { action: 'start_approval', params: actionData.start_approval };
                  }
                  
                  const aType = String(actionData.action || '').toUpperCase();
                  
                  // 💡 Aggressive Auto-execute: catch ANY read-only or query action
                  const safeKeywords = ['QUERY', 'SEARCH', 'STATS', 'COUNT', 'GET', 'LIST', 'VIEW', 'SHOW', 'READ', 'DASHBOARD'];
                  const isSafe = safeKeywords.some(k => aType.includes(k));

                  if (isSafe) {
                    aiMsg.content = aiMsg.content.replace(/```json[\s\S]*?```/g, "").trim();
                    confirmAiAction(actionData, aiStore.editorMessages.length - 1);
                    return; 
                  }

                  if (actionData.action === "start_approval" || aType === "START_APPROVAL") {
                    const params = actionData.params || actionData;
                    
                    // 补全姓名
                    if (!params.approver_names) {
                      const nameMatch = aiMsg.content.match(/\*\*([^\*]{2,10})\*\*/);
                      if (nameMatch) {
                        params.approver_names = nameMatch[1];
                      } else if (params.approvers && Array.isArray(params.approvers)) {
                        const nameList = params.approvers.filter((p: any) => typeof p === 'string');
                        if (nameList.length > 0) params.approver_names = nameList.join(', ');
                      }
                    }

                    // 💡 核心改进：如果只有姓名没有 ID，自动尝试匹配并弹出窗口
                    if (params.approver_names && (!params.approvers || params.approvers.length === 0 || typeof params.approvers[0] === 'string')) {
                      const names = Array.isArray(params.approver_names) ? params.approver_names : String(params.approver_names).split(',');
                      const searchName = (names[0] || "").trim();
                      
                      if (searchName) {
                        api.get('/users', { params: { search: searchName } }).then(res => {
                        let matchedUsers = (res.data.items || []).filter((u: any) => u.id !== auth.user?.id);
                        
                        // 💡 容错处理：如果没搜到，尝试去掉所有空格再搜一次
                        if (matchedUsers.length === 0 && searchName.includes(' ')) {
                          return api.get('/users', { params: { search: searchName.replace(/\s/g, '') } }).then(res2 => {
                            matchedUsers = (res2.data.items || []).filter((u: any) => u.id !== auth.user?.id);
                            return matchedUsers;
                          });
                        }
                        return matchedUsers;
                      }).then(foundList => {
                        if (foundList && foundList.length === 1) {
                          const foundUser = foundList[0];
                          params.approvers = [foundUser.id];
                          params.approver_names = foundUser.display_name;
                          // 💡 此处不再自动弹出窗口，由用户在 AI 聊天框点击“确认执行”
                        } else {
                          console.log("[Editor AI] Search for " + searchName + " returned " + (foundList?.length || 0) + " items");
                        }
                        }).catch(err => {
                          console.error("[Editor AI] User search failed", err);
                        });
                      }
                    }
                    
                    const displayNames = Array.isArray(params.approver_names) ? params.approver_names.join(', ') : params.approver_names;
                    aiMsg.action = {
                      action: "start_approval",
                      confirm_prompt: displayNames ? `立即发起审批：${displayNames}？` : undefined,
                      params: params
                    };
                    aiMsg.content = aiMsg.content.replace(approvalRegex, "").replace(/```json\s*\{[\s\S]*?\}\s*```/, "").trim();
                  }
                } catch(e) {
                  console.error("AI Action parse failed", e);
                }
              }
            }
            if (chatScroll.value) {
              await nextTick();
              const el = (chatScroll.value as any).$el || chatScroll.value;
              el.scrollTop = el.scrollHeight;
            }
          } catch(e) {}
        }
      }
    }
  } catch (err) {
    ElMessage.error(t("common.failed"));
  } finally {
    askingCount.value = Math.max(0, askingCount.value - 1);
  }
}

// 💡 监听消息变化自动滚动
watch(() => aiStore.editorMessages, () => {
  scrollToBottom();
}, { deep: true });

// 💡 监听来自 AI 助理的审批触发事件
onMounted(() => {
  const handler = (e: any) => {
    console.log("[DEBUG] Received edms:trigger_approval", e.detail);
    const { approvers, type } = e.detail;
    if (approvers) {
      // 兼容 ID 可能是字符串的情况
      approverIds.value = approvers.map((id: any) => Number(id));
    }
    if (type) approvalType.value = type;
    showApproval.value = true;
    ElMessage.info(t("editor.ai.preselectedApprovers", "已根据 AI 建议为您预选审批人"));
  };
  window.addEventListener('edms:trigger_approval', handler);
  onBeforeUnmount(() => window.removeEventListener('edms:trigger_approval', handler));
});


const versionList = ref<Array<any>>([]);

const searchVisible = ref(false);
const searchTerm = ref("");
const replaceTerm = ref("");
const pageSettingsVisible = ref(false);

const showApproval = ref(false);
const approvalType = ref("parallel");
const approverIds = ref<number[]>([]);
const userOptions = ref<Array<{ id: number; login_name: string; display_name?: string; department_id?: number }>>([]);
const deptOptions = ref<Array<{ id: number; name: string }>>([]);
const selectedDeptId = ref<number | null>(null);

watch(showApproval, (val) => {
  if (val) {
    selectedDeptId.value = null;
    approverIds.value = [];
  }
});

const page = ref({
  orientation: "portrait",
  marginTop: 40,
  marginBottom: 40,
  showPageNumber: true,
  paperFormat: "A4",
});

const saveHint = ref("");
const collabColors = ref<Array<{ name: string; color: string }>>([]);

const currentFontFamily = ref("Inter, sans-serif");
const currentFontSize = ref("16px");
const currentColor = ref("#000000");
const currentHighlight = ref("#ffffff");

const filterAuthor = ref("");
const filterStatus = ref("all");
const filterDate = ref<string | null>(null);

const authorOptions = computed(() => {
  const set = new Set(comments.value.map(c => c.author_login));
  return Array.from(set);
});

const filteredComments = computed(() => {
  return comments.value.filter(c => {
    if (filterAuthor.value && c.author_login !== filterAuthor.value) return false;
    if (filterStatus.value !== "all" && c.status !== filterStatus.value) return false;
    if (filterDate.value && c.created_at && !c.created_at.startsWith(filterDate.value)) return false;
    return true;
  });
});

const threadedComments = computed(() => {
  const all = filteredComments.value;
  const roots = all.filter(c => !c.parent_id);
  const map: Record<number, any> = {};
  all.forEach(c => { map[c.id] = { ...c, replies: [] }; });
  all.forEach(c => {
    if (c.parent_id && map[c.parent_id]) {
      map[c.parent_id].replies.push(map[c.id]);
    }
  });
  return roots.map(r => map[r.id]);
});

const filteredUserOptions = computed(() => {
  let list = userOptions.value;
  if (auth.user) {
    list = list.filter((u) => u.id !== auth.user!.id);
  }
  if (selectedDeptId.value) {
    list = list.filter((u) => u.department_id === selectedDeptId.value);
  }
  return list;
});


const ydoc = new Y.Doc();
const awareness = new Awareness(ydoc);
const userColor = `#${Math.floor(Math.random() * 0xffffff).toString(16).padStart(6, "0")}`;

// Undo/Redo Manager with 20-step limit
const undoManager = new Y.UndoManager(ydoc.getXmlFragment("default"), {
  limit: 20, // 💡 Robustness: Restored 20-step limit as requested
  captureTimeout: 200 // Consolidate fast edits into one step
} as any);

function doUndo() { 
  if (editor.value) {
    editor.value.chain().focus().undo().run();
  } else {
    undoManager.undo();
  }
}
function doRedo() { 
  if (editor.value) {
    editor.value.chain().focus().redo().run();
  } else {
    undoManager.redo();
  }
}

let collabDisconnect: (() => void) | null = null;
const staticCollabs = ref<Array<{ name: string; color: string }>>([]);

const isMounted = ref(false);
const isLoadingDoc = ref(false);

function refreshCollabList() {
  // 💡 安全检查：如果组件已卸载、文档归档或正在重新加载文档，不再更新协作列表
  if (!isMounted.value || isLoadingDoc.value || meta.value.status === 'approved') return;
  
  const states = awareness.getStates();
  const list: Array<{ name: string; color: string }> = [];
  states.forEach((s) => {
    const u = s.user as any;
    if (u?.name) list.push({ name: u.name, color: u.color || "#888" });
  });
  collabColors.value = list;
}

const editor = useEditor({
  extensions: [
    StarterKit.configure({ 
      history: false // 💡 Disable history because Collaboration handles it
    }),
    Underline, TextStyle, Color, FontFamily, CustomImage, TableRow, TableHeader, TableCell,
    Highlight.configure({ multicolor: true }),
    TextAlign.configure({ types: ["heading", "paragraph", "image"] }),
    Collaboration.configure({ document: ydoc }),
    CollaborationCursor.configure({ provider: { awareness } as never }),
    Table.configure({ resizable: true }),
    FontSize, LineHeight, Indent, CommentMark, TableExit, SearchAndReplace,
    Markdown,
  ],
  editable: true,
  onUpdate: () => scheduleSave(),
  onSelectionUpdate: ({ editor }) => {
    currentFontFamily.value = editor.getAttributes('textStyle').fontFamily || "Inter, sans-serif";
    currentFontSize.value = editor.getAttributes('textStyle').fontSize || "16px";
  }
});

let saveTimer = 0;
function scheduleSave() {
  if (!meta.value.can_edit) return;
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => saveNow(), 2000);
}

function updateSearch() { (editor.value as any)?.commands.setSearchTerm(searchTerm.value); }
function doReplace() {
  (editor.value as any)?.commands.setReplaceTerm(replaceTerm.value);
  (editor.value as any)?.commands.replace();
}
function doReplaceAll() {
  (editor.value as any)?.commands.setReplaceTerm(replaceTerm.value);
  (editor.value as any)?.commands.replaceAll();
}

async function savePageSettings() {
  try {
    await api.patch(`/documents/${docId.value}`, { 
      page_settings_json: JSON.stringify(page.value),
      space_id: selectedSpaceId.value === 'none' ? null : selectedSpaceId.value
    });
    pageSettingsVisible.value = false;
    ElMessage.success(t("editor.pageSettingsSaved"));
    loadDoc(true);
  } catch { ElMessage.error(t("common.failed", "Failed")); }
}



async function startApproval() {
  if (!approverIds.value.length) return ElMessage.warning(t("editor.selectApprovers"));
  
  // 开启转圈
  loading.value = true;
  
  try {
    // 老老实实等待接口返回
    await api.post(`/documents/${docId.value}/approvals`, {
      type: approvalType.value,
      approvers: approverIds.value,
    });
    
    // 成功后关闭弹窗并提示
    showApproval.value = false;
    ElMessage.success(t("editor.approvalStarted"));
    
    // 静默刷新页面数据，让界面变成“审批中”
    await loadDoc(true);
    
  } catch (err) {
    console.error("Start approval failed:", err);
    ElMessage.error(t("common.failed", "Failed"));
  } finally {
    // 4. 无论成功还是网络异常，铁定关闭转圈
    loading.value = false;
  }
}

async function newVersion() {
  try {
    await api.post(`/documents/${docId.value}/new-version`);
    ElMessage.success(t("editor.newVersionOk"));
    loadDoc();
  } catch { ElMessage.error(t("common.failed", "Failed")); }
}

async function loadStaticCollaborators() {
  try {
    const { data } = await api.get(`/documents/${docId.value}/collaborators`);
    staticCollabs.value = data.items.map((item: any) => ({ name: item.name, color: "#888" }));
    if (meta.value.status === 'approved') collabColors.value = staticCollabs.value;
  } catch {}
}

async function loadVersions() {
  const { data } = await api.get(`/documents/${docId.value}/versions`);
  versionList.value = data.items;
}

// Approval logic for approvers opening the doc
const rejectDlg = ref(false);
const rejectReason = ref("");

async function handleEditorApprove() {
  try {
    await api.post(`/approvals/participants/${meta.value.pending_participant_id}/decision`, {
      decision: "approve"
    });
    ElMessage.success(t("inbox.submitted"));
    loadDoc(true);
  } catch (err) {
    ElMessage.error(t("common.failed", "Failed"));
  }
}

function handleEditorReject() {
  rejectReason.value = "";
  rejectDlg.value = true;
}

async function confirmEditorReject() {
  if (!rejectReason.value.trim()) {
    return ElMessage.warning(t("inbox.reasonRequired"));
  }
  try {
    await api.post(`/approvals/participants/${meta.value.pending_participant_id}/decision`, {
      decision: "reject",
      reason: rejectReason.value
    });
    ElMessage.success(t("inbox.submitted"));
    rejectDlg.value = false;
    loadDoc(true);
  } catch (err) {
    ElMessage.error(t("common.failed", "Failed"));
  }
}

async function loadDepts() {
  try {
    const { data } = await api.get("/users/departments");
    deptOptions.value = data;
  } catch {}
}

async function loadSpaces() {
  try {
    const { data } = await api.get("/documents/tree");
    spacesOptions.value = data.items
      .filter((i: any) => i.is_space && !i.is_dept && i.id !== "space_unassigned")
      .map((i: any) => ({ id: i.space_id, name: i.name }));
  } catch {}
}

async function loadDoc(silent = false) {
  if (!silent) loading.value = true;
  isLoadingDoc.value = true; // 🔑 开启同步锁
  console.log("[DEBUG] loadDoc started (silent=" + silent + ")");
  try {
    const { data } = await api.get(`/documents/${route.params.id}`);
    console.log("[DEBUG] Doc data loaded, status:", data.status);
    title.value = data.title;
    meta.value = data;
    selectedSpaceId.value = data.space_id || 'none';
    if (data.page_settings_json) {
        try {
            const ps = typeof data.page_settings_json === 'string' 
                ? JSON.parse(data.page_settings_json) 
                : data.page_settings_json;
            Object.assign(page.value, ps);
        } catch (e) {
            console.error("解析页面设置失败:", e);
        }
    }
    // 防呆设计：允许编辑草稿，或者管理员编辑模板
    const isEditable = data.can_edit && (data.status === 'draft' || data.is_template);
    editor.value?.setEditable(isEditable);
    if (data.yjs_state_b64) {
      Y.applyUpdate(ydoc, Uint8Array.from(atob(data.yjs_state_b64), (c) => c.charCodeAt(0)));
    } else if (data.content_json) {
      console.log("[DEBUG] Loading content from JSON...");
      const j = typeof data.content_json === "string" ? JSON.parse(data.content_json) : data.content_json;
      // 关键：在协作模式下，需要确保编辑器已就绪且稍作延迟以允许插件初始化
      setTimeout(() => {
        if (editor.value) {
          editor.value.commands.setContent(j, true); // true means emit update for collab
          console.log("[DEBUG] Content set successfully.");
        }
      }, 300);
    }
    
    console.log("[DEBUG] Attaching collaboration...");
    collabDisconnect?.(); // 💡 重要：先断开之前的连接，防止监听器堆积
    collabDisconnect = attachDocCollab(
      docId.value, 
      ydoc, 
      awareness, 
      { name: auth.user?.display_name || auth.user?.login_name || "User", color: userColor }
    );
    awareness.on("update", refreshCollabList);
    
    // 并行执行核心任务
    Promise.all([
      loadComments().catch(e => console.error("Load comments failed", e)),
      loadVersions().catch(e => console.error("Load versions failed", e)),
      loadStaticCollaborators().catch(e => console.error("Load collabs failed", e)),
    ]).then(() => {
       console.log("[DEBUG] Core parallel tasks complete.");
    });

    // 延迟加载不紧急的下拉框数据，防止导航卡顿
    setTimeout(() => {
      loadDepts().catch(e => console.error("Load depts failed", e));
      loadSpaces().catch(e => console.error("Load spaces failed", e));
      if (userOptions.value.length === 0) {
        api.get("/users", { params: { size: 1000 } })
          .then(us => { userOptions.value = us.data.items; })
          .catch(e => console.error("Load users failed", e));
      }
    }, 500);

    if (meta.value.status !== 'approved') refreshCollabList();
  } catch (err) {
    console.error("[DEBUG] loadDoc CRITICAL ERROR:", err);
  } finally {
    if (!silent) loading.value = false;
    isLoadingDoc.value = false; // 🔑 释放同步锁
    console.log("[DEBUG] loadDoc finished, loading=false");
  }
}

async function saveNow() {
  if (!editor.value || !meta.value.can_edit) return;
  if (!docId.value || isNaN(docId.value)) {
    console.error("[DEBUG] Attempted to save document with invalid ID:", docId.value);
    return;
  }
  saving.value = true;
  try {
    const content_json = editor.value.getJSON();
    const update = Y.encodeStateAsUpdate(ydoc);
    await api.put(`/documents/${docId.value}/content`, { content_json, yjs_state_b64: btoa(String.fromCharCode(...update)) });
    saveHint.value = t("editor.savedAt", { time: new Date().toLocaleTimeString() });
    
    // 💡 Clear history on save as requested
    undoManager.clear();
  } catch (err) { 
    console.error("Save failed:", err);
    saveHint.value = t("editor.saveFailed"); 
  }
  finally { saving.value = false; }
}

async function saveTitle() { 
  if (!docId.value || isNaN(docId.value)) return;
  try {
    await api.patch(`/documents/${docId.value}`, { title: title.value }); 
  } catch (err) {
    console.error("Title save failed:", err);
  }
}

async function confirmDeleteDoc() {
  try {
    await ElMessageBox.confirm(
      t("editor.deleteDocConfirm"),
      t("common.warning", "Warning"),
      {
        confirmButtonText: t("common.ok", "OK"),
        cancelButtonText: t("inbox.cancel"),
        type: "warning",
      }
    );
    await api.delete(`/documents/${docId.value}`);
    ElMessage.success(t("editor.deleteSuccess"));
    router.push({ name: "library" });
  } catch (err) {
    if (err !== "cancel") {
      ElMessage.error(t("editor.deleteFailed"));
    }
  }
}

async function loadComments() {
  const { data } = await api.get(`/documents/${docId.value}/comments`, { params: { hide_resolved: 0 } });
  comments.value = data.items;
}

async function resolveComment(id: number) {
  await api.patch(`/comments/${id}`, { status: "resolved" });
  loadComments();
}

async function replyTo(parentId: number) {
  const body = (replyMap.value[parentId] || "").trim();
  if (!body) return;
  await api.post(`/documents/${docId.value}/comments`, { body, parent_id: parentId });
  replyMap.value[parentId] = "";
  loadComments();
}

async function importDocx() {
  const input = document.createElement("input");
  input.type = "file"; input.accept = ".docx";
  input.onchange = async (e: any) => {
    const file = e.target.files[0]; if (!file) return;
    try {
      const result = await mammoth.convertToHtml({ arrayBuffer: await file.arrayBuffer() }, {
        convertImage: mammoth.images.imgElement(function(image) {
          return image.read("base64").then(function(imageBuffer) {
            return {
              src: "data:" + image.contentType + ";base64," + imageBuffer
            };
          });
        })
      });
      editor.value?.commands.setContent(result.value);
      ElMessage.success(t("editor.messages.importSuccess"));
    } catch { ElMessage.error(t("editor.messages.importFailed")); }
  };
  input.click();
}

function insertImage() {
  const input = document.createElement("input");
  input.type = "file"; 
  input.accept = "image/*";
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]; 
    if (!file) return;
    
    const formData = new FormData(); 
    formData.append("file", file); 
    
    try {
      // 💡 修改 1：补全蓝图前缀 `/documents`
      // 💡 修改 2：加上 multipart/form-data 请求头
      const { data } = await api.post(`/documents/upload-image`, formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      });
      // 插入图片到编辑器
      (editor.value?.chain().focus() as any).setImage({ src: data.url }).run();
    } catch (err: any) { 
      console.error("上传图片报错详情:", err.response || err);
      ElMessage.error(`图片上传失败: ${err.response?.status === 404 ? '接口不存在' : '后端断开连接'}`); 
    }
  };
  input.click();
}

async function insertCustomTable() {
  try {
    const { value: rs } = await ElMessageBox.prompt(t("editor.messages.insertTableRows"), t("editor.messages.insertTableTitle"), { inputPattern: /^[1-9][0-9]?$/, inputValue: "3", confirmButtonText: t("common.ok"), cancelButtonText: t("common.cancel") });
    const { value: cs } = await ElMessageBox.prompt(t("editor.messages.insertTableCols"), t("editor.messages.insertTableTitle"), { inputPattern: /^[1-9][0-9]?$/, inputValue: "3", confirmButtonText: t("common.ok"), cancelButtonText: t("common.cancel") });
    editor.value?.chain().focus().insertTable({ rows: parseInt(rs), cols: parseInt(cs), withHeaderRow: true }).run();
  } catch {}
}

function setFontSize(val: string) { (editor.value?.chain().focus() as any).setFontSize(val).run(); }
function setFontFamily(val: string) { (editor.value?.chain().focus() as any).setFontFamily(val).run(); }
function setTextColor(e: Event) { (editor.value?.chain().focus() as any).setColor((e.target as HTMLInputElement).value).run(); }
function setHighlight(e: Event) { (editor.value?.chain().focus() as any).toggleHighlight({ color: (e.target as HTMLInputElement).value }).run(); }
function doIndent() { (editor.value?.chain().focus() as any).indent().run(); }
function doOutdent() { (editor.value?.chain().focus() as any).outdent().run(); }
function scrollToComment(id: number) {
  const el = document.querySelector(`.tiptap span[data-comment-id="${id}"]`);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}


async function downloadDocx() {
  try {
    const res = await api.get(`/documents/${docId.value}/export.docx`, { responseType: 'blob' });
    const a = document.createElement("a"); a.href = URL.createObjectURL(res.data); a.download = `doc_${docId.value}.docx`; a.click();
    ElMessage.success(t("editor.exportDocx"));
  } catch { ElMessage.error(t("editor.exportFailed")); }
}
async function downloadPdf() {
  try {
    const res = await api.get(`/documents/${docId.value}/export.pdf`, { responseType: 'blob' });
    const a = document.createElement("a"); a.href = URL.createObjectURL(res.data); a.download = `doc_${docId.value}.pdf`; a.click();
    ElMessage.success(t("editor.exportPdf"));
  } catch { ElMessage.error(t("editor.exportFailed")); }
}

async function addCommentOnSelection() {
  if (!editor.value || editor.value.state.selection.empty) return ElMessage.warning(t("editor.selectTextFirst"));
  try {
    const { value: body } = await ElMessageBox.prompt(t("editor.commentPrompt"), t("editor.newCommentTitle"), { confirmButtonText: t("common.ok"), cancelButtonText: t("common.cancel") });
    if (body) {
      const { from, to } = editor.value.state.selection;
      const { data } = await api.post(`/documents/${docId.value}/comments`, { body, anchor_json: JSON.stringify({ from, to }) });
      (editor.value.chain().focus() as any).setComment(data.id).run();
      loadComments();
    }
  } catch {}
}
function setImgWidth(width: string) {
  if (editor.value) {
    editor.value.chain().focus().updateAttributes('image', { width }).run();
  }
}

const watermarkDataUrl = ref("");
function updateWatermark() {
  if (!auth.user) return;
  const canvas = document.createElement("canvas");
  canvas.width = 400;
  canvas.height = 300;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.rotate((-45 * Math.PI) / 180);
  ctx.fillStyle = "rgba(100, 100, 100, 0.08)";
  ctx.font = "18px Inter, sans-serif";
  ctx.textAlign = "center";
  const text = `${auth.user?.display_name || auth.user?.login_name || 'User'} · ${auth.user?.employee_no || ''} · ${new Date().toLocaleString()}`;
  ctx.fillText(text, 0, 0);
  watermarkDataUrl.value = canvas.toDataURL();
}

const generatingAi = ref(false);
async function handleAiAction(action: string) {
  if (!editor.value || !auth.user) return;
  const selection = editor.value.state.selection;
  const text = editor.value.state.doc.textBetween(selection.from, selection.to, " ");
  if (!text) return ElMessage.warning(t("editor.selectTextFirst", "Please select text"));
  generatingAi.value = true;
  try {
    // Move cursor to the end of selection to avoid replacing original text
    editor.value.chain().focus().setTextSelection(selection.to).insertContent("\n\n").run();
    const startPos = editor.value.state.selection.to;
    const baseUrl = api.defaults.baseURL || "/api";
    const genUrl = baseUrl.endsWith("/") ? `${baseUrl}ai/generate` : `${baseUrl}/ai/generate`;
    const response = await fetch(genUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${auth.token}` },
      body: JSON.stringify({ prompt: text, action, lang: locale.value })
    });
    if (!response.body) throw new Error("No response body");
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let done = false;
    let fullResponse = "";

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        const chunkStr = decoder.decode(value, { stream: true });
        for (const line of chunkStr.split("\n")) {
          if (line.startsWith("data: ")) {
            const raw = line.replace("data: ", "").trim();
            if (raw === "[DONE]" || !raw) continue;
            try {
              const data = JSON.parse(raw);
              if (data.type === "chunk" && data.content) {
                fullResponse += data.content;
                // During streaming, insert as plain text
                editor.value.chain().focus().insertContent(data.content).run();
              } else if (data.type === "done") {
                // Generation complete. Replace the raw text with correctly parsed HTML.
                const currentPos = editor.value.state.selection.to;
                const html = marked.parse(fullResponse);
                
                // Delete the raw text chunks we just inserted and replace with HTML
                editor.value.chain()
                  .focus()
                  .deleteRange({ from: startPos, to: currentPos })
                  .insertContent(html)
                  .run();
                  
                done = true;
                break;
              }
            } catch(e) {
              console.warn("Parse error in handleAiAction:", e);
            }
          }
        }
      }
    }
  } catch (err) {
    ElMessage.error("AI generation failed");
  } finally { generatingAi.value = false; }
}

const onStatusChanged = (e: any) => {
  if (!isMounted.value) return; // 💡 保护逻辑
  const data = e.detail;
  console.log("[DEBUG] Status changed event received:", data);
  if (data.status === "in_approval") {
    // 💡 只有当自己没在 Loading（不是操作发起者）时，才协助关闭弹窗
    if (!loading.value) {
      showApproval.value = false;
    }
    
    meta.value.status = "in_approval";
    meta.value.can_edit = false;
    editor.value?.setEditable(false);
    ElMessage.success(t("editor.approvalStarted"));
  } else if (data.can_edit !== undefined) {
    meta.value.status = data.status;
    meta.value.can_edit = data.can_edit;
    editor.value?.setEditable(data.can_edit);
    if (data.status) {
      ElMessage.info(t("editor.statusChanged", { status: data.status }));
    }
  }
};

const onInsertContent = (e: any) => {
  if (!isMounted.value || !editor.value) return;
  const { content } = e.detail;
  if (content) {
    const html = marked.parse(content);
    editor.value.chain().focus().insertContent(html).run();
  }
};

onMounted(() => {
  isMounted.value = true;
  loadDoc();
  updateWatermark();
  setInterval(updateWatermark, 60000);
  window.addEventListener("edms:status_changed", onStatusChanged);
  window.addEventListener("edms:insert_content", onInsertContent);
});
onBeforeUnmount(() => { 
  isMounted.value = false;
  collabDisconnect?.(); 
  awareness.off("update", refreshCollabList); 
  editor.value?.destroy(); 
  window.removeEventListener("edms:status_changed", onStatusChanged);
  window.removeEventListener("edms:insert_content", onInsertContent);
});
</script>

<style scoped>
.editor-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
  background-color: var(--el-bg-color-page, #f5f7fa);
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: white;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.status-tag { margin-left: 8px; }
.hint { font-size: 12px; color: var(--el-text-color-secondary); }

.collab-avatars {
  display: flex;
  margin-right: 16px;
}
.avatar-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  border: 2px solid white;
  margin-left: -8px;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.avatar-dot:first-child { margin-left: 0; }

.editor-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 8px 16px;
  background-color: white;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.toolbar-divider {
  width: 1px;
  height: 24px;
  background-color: var(--el-border-color-lighter);
  margin: 0 4px;
}
.toolbar-group .el-button {
  padding: 5px 8px;
}
.toolbar-group .el-button.is-active {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-5);
}

.body {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.main-wrapper {
  flex: 1;
  overflow: auto; /* 保证出现滚动条 */
  padding: 32px;
  display: flex;
  justify-content: center;
  align-items: flex-start; /* 关键1：顶部对齐，允许底部无限生长 */
}

.pdf-view-wrapper {
  width: 100%;
  max-width: 1000px;
  height: calc(100vh - 160px);
  background: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  border-radius: 8px;
  overflow: hidden;
}

.pdf-frame {
  width: 100%;
  height: 100%;
}

.main-paper {
  position: relative;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  min-height: 800px; /* 纸张的初始最小高度 */
  height: auto !important; /* 关键2：强制高度由内部文字撑开，覆盖之前的限制 */
  flex-shrink: 0; /* 关键3（最核心）：禁止这块白纸在 flex 容器中被压缩！！ */
  box-sizing: border-box;
  padding: 40px;
  padding-bottom: 80px; 
  transition: width 0.3s ease;
}

/* 分页符在编辑器里的长相 */
/* 让分页符变成“两张纸中间的物理灰色缝隙” */
:deep(hr.page-break) {
  border: none;
  /* 用和网页背景一样的灰色，制造“纸张断层”的视觉假象 */
  background-color: var(--el-bg-color-page, #f5f7fa);
  height: 40px; /* 两张纸之间的灰色距离 */
  margin: 40px -40px; /* 撑满整个白纸的宽度，抵消 padding */
  page-break-after: always;
  position: relative;
  clear: both;
  cursor: default;
  z-index: 1;
}

/* 模拟上一张纸的底部边缘和阴影 */
:deep(hr.page-break::before) {
  content: '';
  position: absolute;
  top: -1px;
  left: 0;
  right: 0;
  border-top: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 -2px 6px rgba(0,0,0,0.05);
}

/* 模拟下一张纸的顶部边缘和阴影 */
:deep(hr.page-break::after) {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.main-paper.A4 { width: 794px; }
.main-paper.Letter { width: 816px; min-height: 1056px; }
.main-paper.Legal { width: 816px; min-height: 1344px; }

.side {
  width: 320px;
  background-color: white;
  border-left: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
:deep(.el-tabs) {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
}
:deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
:deep(.el-tab-pane) {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.comments-header {
  padding: 8px 16px;
}
.comment-filters {
  padding: 8px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background-color: #fafafa;
}
.comments-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
}

.comment-group { margin-bottom: 12px; }
.comment {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 12px;
  background-color: white;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.comment:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.comment.resolved { opacity: 0.6; }
.meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
}
.comment-body { margin-bottom: 8px; font-size: 14px; }

.replies {
  margin-left: 20px;
  border-left: 2px solid #f0f0f0;
  padding-left: 12px;
  margin-top: 4px;
}
.comment.reply {
  padding: 8px 10px;
  margin-top: 4px;
  font-size: 13px;
  background-color: #fafafa;
}
.comment.reply .comment-body { margin-bottom: 0; }

.version-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.version-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
}
.version-items {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
}
.version-item {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: default;
}
.v-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}
.v-no { font-weight: bold; color: var(--el-color-primary); }
.v-user { font-size: 12px; color: var(--el-text-color-secondary); }
.v-time { font-size: 11px; color: var(--el-text-color-placeholder); }

.tiptap { outline: none; }
.tiptap :deep(.ProseMirror) {
  outline: none;
  min-height: 100%;
  height: auto !important; /* 关键4：确保 Tiptap 编辑器本身高度能自动增长 */
}
.tiptap :deep(table) {
  border-collapse: collapse;
  table-layout: fixed;
  width: 100%;
  margin: 0;
  overflow: hidden;
}
.tiptap :deep(table td), .tiptap :deep(table th) {
  min-width: 1em;
  border: 1px solid var(--el-border-color-darker);
  padding: 3px 5px;
  vertical-align: top;
  box-sizing: border-box;
  position: relative;
}
.tiptap :deep(.search-result) { background-color: #ffde5e; }

.search-bar {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  background-color: #f0f2f5;
  border-bottom: 1px solid var(--el-border-color-lighter);
  align-items: center;
}

.tiptap :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  display: block;
}
.tiptap :deep(img[style*="text-align: center"]) {
  margin-left: auto;
  margin-right: auto;
}
.tiptap :deep(img[style*="text-align: right"]) {
  margin-left: auto;
  margin-right: 0;
}
.tiptap :deep(img[style*="text-align: left"]) {
  margin-right: auto;
  margin-left: 0;
}
.tiptap :deep(img.ProseMirror-selectednode) {
  outline: 3px solid var(--el-color-primary);
}

.ai-bubble-menu {
  display: flex;
  background-color: white;
  padding: 4px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  border: 1px solid var(--el-border-color-lighter);
}
.ai-btn { font-weight: bold; }
.watermark-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  z-index: 15;
  background-repeat: repeat;
  opacity: 0.8;
}

/* AI Panel Styles */
.ai-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  padding: 12px;
  overflow: hidden;
}

.ai-tags-section {
  margin-bottom: 20px;
  background: var(--el-color-primary-light-9);
  padding: 12px;
  border-radius: 8px;
  border: 1px dashed var(--el-color-primary);
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ai-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.ai-tag:hover {
  transform: scale(1.05);
  border-color: var(--el-color-primary);
}

.empty-tags {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-style: italic;
}

.ai-chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--el-fill-color-extra-light);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-msg {
  max-width: 85%;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
}

.chat-msg.user {
  align-self: flex-end;
  background-color: var(--el-color-primary);
  color: white;
  border-bottom-right-radius: 2px;
}

.chat-msg.ai {
  align-self: flex-start;
  background-color: white;
  color: var(--el-text-color-primary);
  border: 1px solid var(--el-border-color-lighter);
  border-bottom-left-radius: 2px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}

.chat-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-input-area {
  padding: 12px;
  background: white;
  border-top: 1px solid var(--el-border-color-lighter);
}

.chat-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

/* AI Action Card Styles */
.ai-action-card {
  margin-top: 12px;
  background: white;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.ai-action-card .card-header {
  background: var(--el-color-primary-light-9);
  padding: 6px 12px;
  border-bottom: 1px solid var(--el-color-primary-light-7);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: bold;
  color: var(--el-color-primary);
}

.ai-action-card .card-body {
  padding: 12px;
}

.ai-action-card .action-desc {
  font-size: 13px;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
  line-height: 1.4;
}

.ai-action-card .action-meta {
  margin-bottom: 8px;
}

.ai-action-card .card-actions {
  padding: 8px 12px;
  background: var(--el-fill-color-extra-light);
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.msg-enter-active {
  transition: all 0.3s ease;
}
.msg-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: var(--el-color-primary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
  opacity: 0.6;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); opacity: 1; }
}
</style>
