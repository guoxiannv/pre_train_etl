import os
import re
import json
import streamlit as st
st.set_page_config(layout="wide", initial_sidebar_state="expanded")
# st.set_option('deprecation.showPyplotGlobalUse', False)
import traceback
import time

# 添加CSS样式用于按钮
st.markdown("""
<style>
    /* 顶部和底部导航按钮 */
    .floating-button {
        position: fixed;
        right: 30px;
        z-index: 1000;
        border-radius: 50%;
        width: 45px;
        height: 45px;
        text-align: center;
        line-height: 45px;
        font-size: 20px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.5);
        cursor: pointer;
        transition: all 0.3s;
        background-color: rgba(60, 60, 60, 0.7);
        color: white;
    }
    .top-button {
        bottom: 90px;
    }
    .bottom-button {
        bottom: 30px;
    }
    .floating-button:hover {
        box-shadow: 3px 3px 10px rgba(0,0,0,0.7);
        transform: scale(1.05);
        background-color: rgba(80, 80, 80, 0.9);
    }
    
    .json-control-buttons {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        margin-top: 5px;
    }
    /* 美化JSON控制按钮 */
    .stButton>button {
        border-radius: 4px;
        transition: all 0.2s;
        width: 100%;
        margin-bottom: 8px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    /* 侧边栏控制按钮样式 */
    .sidebar .stButton>button[data-baseweb="button"]:has(div:contains("上一条")) {
        background-color: #339af0;
        color: white;
    }
    .sidebar .stButton>button[data-baseweb="button"]:has(div:contains("下一条")) {
        background-color: #339af0;
        color: white;
    }
    .sidebar .stButton>button[data-baseweb="button"]:has(div:contains("查看指定JSON")) {
        background-color: #20c997;
        color: white;
        font-weight: bold;
    }
    /* 按钮样式 - 搜索结果中的显示/隐藏按钮 */
    button[data-baseweb="button"]:has(div:contains("显示该JSON")) {
        background-color: #4a4a4a;
        color: white;
    }
    button[data-baseweb="button"]:has(div:contains("隐藏JSON")) {
        background-color: #555555;
        color: white;
    }
    /* 按钮样式 - 内联JSON显示中的上一条/下一条按钮 */
    .inline-json-display button[data-baseweb="button"]:has(div:contains("上一条")) {
        background-color: #4a4a4a;
        color: white;
    }
    .inline-json-display button[data-baseweb="button"]:has(div:contains("下一条")) {
        background-color: #4a4a4a;
        color: white;
    }
    /* 侧边栏分隔线 */
    .sidebar hr {
        margin-top: 1rem;
        margin-bottom: 1rem;
        border: 0;
        border-top: 2px solid rgba(0,0,0,0.1);
    }
    /* 侧边栏标题样式 */
    .sidebar .block-container h2 {
        color: #1e88e5;
        margin-top: 1rem;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    /* 文件信息显示样式 - 支持深色模式 */
    .file-info {
        background-color: rgba(38, 39, 48, 0.2);
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 4px solid #1e88e5;
        color: inherit;
    }
    .file-info strong {
        color: inherit;
    }
    /* 深色模式下的样式调整 */
    @media (prefers-color-scheme: dark) {
        .file-info {
            background-color: rgba(255, 255, 255, 0.1);
            border-left: 4px solid #64b5f6;
        }
    }
    /* 搜索结果内联JSON显示样式 */
    .inline-json-display {
        margin-left: 20px;
        border-left: 3px solid #666;
        padding-left: 10px;
        margin-bottom: 20px;
    }
    /* 定位锚点样式 */
    #top-anchor {
        position: absolute;
        top: -100px;
        left: 0;
        height: 1px;
        width: 1px;
    }
    #bottom-anchor {
        margin-top: 50px;
        padding-bottom: 100px;
    }
</style>

<!-- 使用ID选择器来增强锚点的可靠性 -->
<div id="top-anchor"></div>
<a href="#top-anchor" class="floating-button top-button">↑</a>
<a href="#bottom-anchor" class="floating-button bottom-button">↓</a>
""", unsafe_allow_html=True)

class show_jsonl:
    def __init__(self):
        if hasattr(st.session_state, "JSONL_DIR") and st.session_state["JSONL_DIR"] and \
           hasattr(st.session_state, "jsonl_dir_input") and st.session_state.jsonl_dir_input.split(",") == st.session_state["JSONL_DIR"]:
            return
        st.session_state["JSONL_DIR"] = st.session_state.jsonl_dir_input.split(",") if hasattr(st.session_state, "jsonl_dir_input") else "" # 多个路径用逗号隔开
        st.session_state["search_results"] = []  # 用于保存搜索结果
        st.session_state["time_taken"] = 0
        st.session_state["jsonl_files"] = []  # 用于保存所有的 JSONL 文件路径
        st.session_state["jsonl_files_contents"] = []  # 用于保存所有的 JSONL 文件的内容 # 可能会比较大
        st.session_state["jsonl_files_display"] = []  # 确保初始化显示路径列表
        st.session_state["path_mapping"] = {}  # 确保初始化路径映射
        st.session_state["search_process"] = 0
        st.session_state["search_process_gap"] = 100

    def load_jsonl_files(self):
        st.session_state["jsonl_files"] = []  # 用于保存所有的 JSONL 文件路径
        st.session_state["jsonl_files_contents"] = []  # 用于保存所有的 JSONL 文件的内容 # 可能会比较大
        st.session_state["jsonl_files_display"] = []  # 用于保存用于显示的相对路径
        st.session_state["path_mapping"] = {}  # 映射相对路径到绝对路径
        
        for dir_path in st.session_state["JSONL_DIR"]:
            base_dir = os.path.abspath(dir_path)
            for root, _, files in (os.walk(dir_path) if os.path.isdir(dir_path) else [(os.path.dirname(dir_path), "", [os.path.basename(dir_path)])]):
                for file in files:
                    if file.lower().endswith(".jsonl"):
                        file_path = os.path.join(root, file)
                        # 保存绝对路径用于实际操作
                        st.session_state["jsonl_files"].append(file_path)
                        
                        # 创建相对路径用于显示
                        try:
                            rel_path = os.path.relpath(file_path, base_dir)
                            # 如果相对路径太短，就加上最后一级目录名
                            if len(rel_path) < len(file) + 5:  # 如果相对路径几乎等于文件名
                                parent_dir = os.path.basename(os.path.dirname(file_path))
                                if parent_dir:
                                    rel_path = os.path.join(parent_dir, rel_path)
                            display_path = f"{os.path.basename(base_dir)}/{rel_path}"
                        except:
                            # 如果出错，使用文件名加父目录
                            display_path = f"{os.path.basename(os.path.dirname(file_path))}/{file}"
                        
                        st.session_state["jsonl_files_display"].append(display_path)
                        st.session_state["path_mapping"][display_path] = file_path
                        
                        # 加载文件内容
                        with open(file_path, "r", encoding = "utf-8") as f:
                            st.session_state["jsonl_files_contents"].append(f.readlines())

    def show_search_bar(self):
        def clear_checkbox(need_clear_box): # 互斥清除
            st.session_state[need_clear_box] = 0
            
        # 监听搜索输入框的变化
        def on_search_input_change():
            # 当搜索关键字发生变化时，清除之前查看的指定JSON状态
            if "current_json_file" in st.session_state:
                del st.session_state["current_json_file"]
            if "current_json_row" in st.session_state:
                del st.session_state["current_json_row"]
                
        st.sidebar.subheader("JSONL查看/搜索工具")
        jsonl_dir_input = st.sidebar.text_input("📂 JSONL搜索路径(多个路径请用,隔开)", on_change=lambda:self.__init__(), key = "jsonl_dir_input")
        jsonl_dir_input_button = st.sidebar.button("加载目录", key = "jsonl_dir_input_button")
        if jsonl_dir_input_button:
            self.load_jsonl_files()
            st.session_state["prev_search_query"] = ""

        if not hasattr(st.session_state, "prev_search_query"):
            st.session_state["prev_search_query"] = ""
        if not hasattr(st.session_state, "prev_search_option"):
            st.session_state["prev_search_option"] = (-1, -1, -1)
        search_query = st.sidebar.text_input("🔎 输入搜索关键字", key="search_query", on_change=on_search_input_change)
        
        # 将搜索选项放在一个扩展器中，使界面更整洁
        with st.sidebar.expander("搜索选项", expanded=False):
            case_sensitive = st.checkbox("区分大小写")
            token_match = st.checkbox("全字匹配", on_change = lambda: clear_checkbox("use_regex_button"), key = "token_match_button")
            use_regex = st.checkbox("使用正则表达式", on_change = lambda: clear_checkbox("token_match_button"),  key = "use_regex_button")
        
        # 添加一条分隔线
        st.sidebar.markdown("---")
        st.sidebar.subheader("直接查看JSON")
        
        jsonl_select = ""
        display_select = ""
        if jsonl_dir_input:
            # 确保这些键存在于session_state中
            if "jsonl_files" not in st.session_state:
                st.session_state["jsonl_files"] = []
            if "jsonl_files_display" not in st.session_state:
                st.session_state["jsonl_files_display"] = []
            if "path_mapping" not in st.session_state:
                st.session_state["path_mapping"] = {}
                
            if len(st.session_state["jsonl_files"]) == 0:
                tip = '(路径下无文件或未加载目录)'
            else:
                tip = f'(当前路径: {len(st.session_state["jsonl_files"])} 个文件)'
            
            # 使用相对路径显示而不是绝对路径
            display_select = st.sidebar.selectbox("📄 选择JSONL文件" + tip, st.session_state["jsonl_files_display"])
            
            # 转换回绝对路径用于实际操作
            if display_select and display_select in st.session_state["path_mapping"]:
                jsonl_select = st.session_state["path_mapping"][display_select]
            
        maxDataIndex = 0
        if jsonl_select and st.session_state.get("jsonl_files", []) and st.session_state.get("jsonl_files_contents", []):
            maxDataIndex = len(st.session_state["jsonl_files_contents"][st.session_state["jsonl_files"].index(jsonl_select)])
            
            # 定义按钮回调函数
            def view_json_callback():
                # 设置当前行数和文件路径
                st.session_state["current_json_file"] = jsonl_select
                st.session_state["current_json_row"] = st.session_state["row_select"]
                # 清除搜索关键字
                if "search_query" in st.session_state:
                    st.session_state["search_query"] = ""
                if "displayed_search_json" in st.session_state:
                    st.session_state["displayed_search_json"] = None
                    
            # 使用表单来捕获回车键 - 表单只包含行号输入和查看按钮
            with st.sidebar.form(key="row_select_form"):
                # 从0开始的行号选择器
                row_select = st.number_input(
                    f"🔢 选择行号 (0-{maxDataIndex-1})", 
                    min_value=0, 
                    max_value=maxDataIndex-1, 
                    value=0,
                    key="row_select"
                )
                
                # 将表单提交按钮修改为与查看JSON功能一致的按钮
                st.form_submit_button("👁️ 查看指定JSON", 
                                     use_container_width=True,
                                     on_click=view_json_callback)
            
            # 移除表单外的重复按钮
            # 添加分隔线
            st.sidebar.markdown("---")

        if search_query:
            # 如果有搜索关键字，清除查看指定JSON的状态
            if "current_json_file" in st.session_state:
                del st.session_state["current_json_file"]
            if "current_json_row" in st.session_state:
                del st.session_state["current_json_row"]
                
            if st.session_state["prev_search_query"] != search_query or st.session_state["prev_search_option"] != (token_match, case_sensitive, use_regex):
                self.perform_search(search_query, token_match, case_sensitive, use_regex)
            self.show_search_result(search_query, token_match, case_sensitive, use_regex)

    def perform_search(self, query, token_match, case_sensitive, use_regex):
        search_results = []
        t0 = time.time()
        if len(st.session_state.get("jsonl_files", [])) == 0:
            return
        for jsonl_index, jsonl_file in enumerate(st.session_state["jsonl_files"]):
            f = st.session_state["jsonl_files_contents"][jsonl_index]
            for line_number, line in enumerate(f):  # 从0开始的行号
                try:
                    # json_data = json.loads(line)
                    # 如果匹配成功，将结果添加到 search_results 中
                    ret, content = self.is_match(line, query, token_match, case_sensitive, use_regex)
                    if ret:
                        search_results.append({
                            "file": jsonl_file,
                            "line_number": line_number,  # 保存0-based行号
                            "content": content.replace('\n', '\\n'),
                        })
                except:
                    # 忽略无效的 JSON 行
                    print(traceback.format_exc())
                    print("[ERROR] json load failed!", jsonl_file, line_number)

        st.session_state["search_results"] = search_results
        st.session_state["time_taken"] = time.time() - t0
        st.session_state["search_process"] = 0

    def show_search_result(self, search_query, token_match, case_sensitive, use_regex):
        # 在这里展示搜索结果
        button_key = 0
        if not hasattr(st.session_state, "search_query") or not st.session_state.search_query:
            return
        if hasattr(st.session_state, "search_results"):
            prev_file_name = ""
            if len(st.session_state.search_results) == 0:
                st.write(f"关键字`{st.session_state.search_query}`未找到任何结果")
                return
            else:
                st.session_state["prev_search_query"] = st.session_state.search_query
                st.session_state["prev_search_option"] = (token_match, case_sensitive, use_regex)

                min_page = 0
                max_page = len(st.session_state.search_results) // st.session_state["search_process_gap"]
                if len(st.session_state.search_results) % st.session_state["search_process_gap"] == 0: max_page -= 1
                if max_page < 0: max_page = 0
                if min_page != max_page:
                    st.session_state["search_process"] = st.slider(
                        "search_process",
                        min_value=min_page,
                        max_value=max_page,
                        # value=st.session_state["search_process"], # 会有时序
                        label_visibility="collapsed")
                start = st.session_state["search_process"] * st.session_state["search_process_gap"]
                end = min(start + st.session_state["search_process_gap"], len(st.session_state.search_results))
                st.write(f"关键字`{st.session_state.search_query}`找到{len(st.session_state.search_results)}个结果，第{st.session_state['search_process']}页显示[{start},{end-1}]范围，耗时{st.session_state['time_taken']:.4f}s")

            # 添加一个会话状态变量来跟踪当前展示的JSON
            if "displayed_search_json" not in st.session_state:
                st.session_state["displayed_search_json"] = None

            for i in range(start, end):
                result = st.session_state.search_results[i]
                result_id = f"{result['file']}:{result['line_number']}"
                
                # 获取用于显示的相对路径
                file_display = result['file']  # 默认使用绝对路径
                # 确保path_mapping存在
                if "path_mapping" in st.session_state:
                    for disp_path, abs_path in st.session_state["path_mapping"].items():
                        if abs_path == result['file']:
                            file_display = disp_path
                            break
                
                if prev_file_name != result['file']:
                    st.write(f"**文件路径：** {file_display}")
                st.write(f"**行号：** {result['line_number']}  `{result['content']}`")
                
                # 添加点击显示该文件的功能
                button_key += 1
                
                # 定义按钮回调函数
                def show_json_callback(result_id=result_id):
                    # 切换显示状态 - 如果当前已经显示这个结果，则隐藏；否则显示这个结果
                    if st.session_state["displayed_search_json"] == result_id:
                        st.session_state["displayed_search_json"] = None
                    else:
                        st.session_state["displayed_search_json"] = result_id
                
                # 创建显示按钮 - 根据当前是否已经展开来显示不同文本
                button_text = "隐藏JSON" if st.session_state["displayed_search_json"] == result_id else "显示该JSON"
                st.button(button_text, key=f"toggle_json_button_{button_key}", 
                          on_click=show_json_callback)
                
                # 如果当前结果被选中显示，则在此处显示JSON内容
                if st.session_state["displayed_search_json"] == result_id:
                    with st.container():
                        st.markdown('<div class="inline-json-display">', unsafe_allow_html=True)
                        try:
                            # 获取文件内容
                            file_idx = st.session_state["jsonl_files"].index(result['file'])
                            file_contents = st.session_state["jsonl_files_contents"][file_idx]
                            line = file_contents[result['line_number']]  # 使用0-indexed行号
                            json_data = json.loads(line)
                            
                            # 显示文件和行号信息
                            st.info(f"📃 **{file_display} - 第 {result['line_number']} 行**")
                            
                            # 移除上一条/下一条按钮，只显示JSON内容
                            for key, value in json_data.items():
                                st.write(f"**{key}:**")
                                st.code(value, language="c")
                            
                        except Exception as e:
                            st.error(f"加载JSON内容时出错: {str(e)}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                
                prev_file_name = result['file']

    def show_json(self, jsonl_path, row):
        # 保存当前显示的文件和行号 (行号从0开始)
        st.session_state["current_json_file"] = jsonl_path
        st.session_state["current_json_row"] = row
        
        f = st.session_state["jsonl_files_contents"][st.session_state["jsonl_files"].index(jsonl_path)]
        # 直接使用0-based索引
        line = f[row]
        json_data = json.loads(line)
        
        # 获取用于显示的相对路径
        display_path = os.path.basename(jsonl_path)  # 默认至少显示文件名
        # 从显示映射中查找相对路径
        if "path_mapping" in st.session_state:
            for disp_path, abs_path in st.session_state["path_mapping"].items():
                if abs_path == jsonl_path:
                    display_path = disp_path
                    break
        
        # 检查是否在显示搜索结果，只有不在搜索结果模式时才显示控制面板
        if not st.session_state.get("search_query", ""):
            # 定义回调函数
            def on_prev_click():
                # 更新行号到上一条 (行号从0开始)
                if row > 0:
                    st.session_state["current_json_row"] = row - 1
                    
            def on_next_click():
                # 更新行号到下一条 (行号从0开始)
                if row < len(f) - 1:
                    st.session_state["current_json_row"] = row + 1
            
            # 在侧边栏添加控制按钮
            with st.sidebar:
                st.subheader("JSON控制面板")
                
                # 使用更美观且适合深色模式的方式显示文件信息
                st.markdown(f"""
                <div class="file-info">
                    <div><strong>文件:</strong> {display_path}</div>
                    <div><strong>位置:</strong> 第 <span style="font-weight:bold;color:#ff9800;">{row}</span> 行 / 共 <span style="font-weight:bold;color:#ff9800;">{len(f)}</span> 行</div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    # 上一条按钮
                    prev_disabled = row <= 0
                    st.button("⬆️ 上一条", key=f"prev_json_{row}", 
                             disabled=prev_disabled, on_click=on_prev_click)
                
                with col2:
                    # 下一条按钮
                    max_row = len(f)
                    next_disabled = row >= max_row - 1
                    st.button("⬇️ 下一条", key=f"next_json_{row}", 
                             disabled=next_disabled, on_click=on_next_click)
                
                st.markdown("---")
        
        # 显示文件名和当前位置信息在主页面
        st.write(f"**当前显示：** {display_path} - 第 {row} 行")
        
        # 显示JSON内容
        for key, value in json_data.items():
            st.write(f"**{key}:**")
            # print(repr(key))
            st.code(value, language="c")
            # print(repr(value))
            # print("-"*80)

    def tokenization_text_to_set(self, text, pattern = re.compile(r"[\w_]+", re.ASCII)):
        return { match.group() for match in pattern.finditer(text) }

    def is_match(self, line, query, token_match, case_sensitive, use_regex, preview_len = 88):
        # 获取需要搜索的字段，当前是搜索json字典中所有key: values的值
        text = line # "\n\n".join([f"{k}: {v}" for k, v in json_data.items()])
        if case_sensitive:
            text_csed = text
            query_csed = query
        else:
            text_csed = text.lower()
            query_csed = query.lower()

        suf = ""
        prf = ""
        if token_match or use_regex:
            if token_match: pattern = re.compile('\\b'+query_csed+'\\b')
            elif use_regex: pattern = re.compile(query_csed)
            re_ret = pattern.search(text_csed)
            ret = bool(re_ret)
            if not ret:
                return ret, ""
            s, e = re_ret.span()
            q_len = e - s
            if q_len > preview_len: # 毁灭吧
                return ret, "..." + text[s:e] + "..."
            if len(text_csed) < preview_len:
                q_s_idx = 0
                q_e_idx = len(text_csed)
            else:
                gap = ((preview_len-q_len)//2)
                q_s_idx = s - gap
                q_e_idx = e + gap
                if q_s_idx < 0:
                    q_s_idx = 0
                    q_e_idx -= q_s_idx
                else:
                    suf = "..."
                if q_e_idx > len(text_csed):
                    q_e_idx = len(text_csed)
                else:
                    prf = "..."
            return ret, suf + text[q_s_idx:q_e_idx] + prf
        else:
            ret = query_csed in text_csed
            if not ret:
                return ret, ""
            if len(query_csed) > preview_len: # 毁灭吧
                return ret, "..." + query + "..."
            if len(text_csed) < preview_len:
                q_s_idx = 0
                q_e_idx = len(text_csed)
            else:
                gap = ((preview_len-len(query_csed))//2)
                q_s_idx = text_csed.index(query_csed) - gap
                q_e_idx = text_csed.index(query_csed) + len(query_csed) + gap
                if q_s_idx < 0:
                    q_s_idx = 0
                    q_e_idx -= q_s_idx
                else:
                    suf = "..."
                if q_e_idx > len(text_csed):
                    q_e_idx = len(text_csed)
                else:
                    prf = "..."
            return ret, suf + text[q_s_idx:q_e_idx] + prf

    def layout(self):
        # 确保基础session_state变量已初始化
        for key in ["jsonl_files", "jsonl_files_display", "jsonl_files_contents", "path_mapping"]:
            if key not in st.session_state:
                st.session_state[key] = []
                
        # 首先显示侧边栏的搜索功能
        self.show_search_bar()
        
        # 搜索模式和查看指定JSON模式互斥，只有当没有搜索关键字时才显示指定JSON
        if not st.session_state.get("search_query", "") and "current_json_row" in st.session_state and "current_json_file" in st.session_state:
            # 确认文件仍然存在于加载的列表中
            if (st.session_state["jsonl_files"] and 
                st.session_state["current_json_file"] in st.session_state["jsonl_files"]):
                file_idx = st.session_state["jsonl_files"].index(st.session_state["current_json_file"])
                
                # 确认行号有效 (行号从0开始)
                row = st.session_state["current_json_row"]
                if (st.session_state["jsonl_files_contents"] and 
                    file_idx < len(st.session_state["jsonl_files_contents"]) and
                    row >= 0 and row < len(st.session_state["jsonl_files_contents"][file_idx])):
                    # 显示JSON内容
                    self.show_json(st.session_state["current_json_file"], st.session_state["current_json_row"])
        
        # 添加底部标记，确保底部导航按钮有足够的空间
        st.markdown('<div id="bottom-anchor"></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    show_jsonl().layout()