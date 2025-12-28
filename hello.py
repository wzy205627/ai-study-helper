import mimetypes
# 1. 强行修正 Windows 的注册表错误
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

import streamlit as st

st.title("终于修好了！🎉")
st.write("如果能看到这句话，说明 Windows 的注册表 Bug 被解决了。")