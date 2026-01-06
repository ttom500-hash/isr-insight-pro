
TypeError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/isr-insight-pro/app.py", line 66, in <module>
    load_css()
    ~~~~~~~~^^
File "/mount/src/isr-insight-pro/app.py", line 13, in load_css
    st.markdown("""
    ~~~~~~~~~~~^^^^
        <style>
        ^^^^^^^
    ...<48 lines>...
        </style>
        ^^^^^^^^
    """, unsafe_allow_status=True)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/streamlit/runtime/metrics_util.py", line 531, in wrapped_func
    result = non_optional_func(*args, **kwargs)
