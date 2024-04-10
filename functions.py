import streamlit as st
from datetime import datetime, timedelta
import re
import smtplib
from email.mime.text import MIMEText
from PIL import Image
import numpy as np
import warnings
import pdfkit
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


warnings.filterwarnings("ignore")

bot_avatar = Image.open("./assets/bot-avatar.png")


def send_email(df):
    # Email configuration
    sender_email = "ekounseken@gmail.com"
    receiver_email = "ekounseken@gmail.com"
    password = "pkyy jfsp xgzj ghbu"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Create a multipart message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Specific Data Update"

    # Text part of the email
    body = """
    The list of updated data:

    {}
    """.format(
        df.to_html(index=False)
    )
    msg.attach(MIMEText(body, "html"))

    # Connect to the SMTP server
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)

    print("Email sent successfully.")


def get_local_time_greeting() -> str:
    # Get the current local time
    current_time = datetime.now().time()

    # Extract the hour from the current time
    hour = current_time.hour

    # Determine the appropriate greeting based on the hour
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    elif 17 <= hour < 20:
        greeting = "Good evening"
    else:
        greeting = "Good night"

    return greeting


def is_valid_email(email: str) -> bool:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def is_valid_us_phone_number(phone_number: str) -> bool:
    # Regular expression pattern for US phone numbers
    pattern = r"^\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$"

    # Check if the phone number matches the pattern
    return re.match(pattern, phone_number) is not None


def validate_required(fields: list, result: dict) -> list[str]:
    error_fields = []
    for field in fields:
        field_name = field["field_name"]

        message = field["message"]
        if "required" in field.keys() and field["required"]:
            if (
                result[field_name] == ""
                or result[field_name] == []
                or result[field_name] is None
            ):
                error_fields.append(message)

    return error_fields


def show_required_error_message(error_fields: list[str]) -> None:
    st.error("Please fill the required fields:", icon="‼️")
    st.write("<ul>", unsafe_allow_html=True)
    for error_field in error_fields:
        st.write(f"<li>{error_field}</li>", unsafe_allow_html=True)
    st.write("</ul>", unsafe_allow_html=True)


def validate_dtype(fields: list, result: dict) -> list[str]:
    error_dtypes = []
    for field in fields:
        field_name = field["field_name"]
        specific_type = field.get("specific_type")

        if specific_type is not None:

            message = field["message"]
            value = result[field_name]

            if value != "":
                if specific_type == "email":
                    if not is_valid_email(value):
                        error_dtypes.append(("email", message))
                elif specific_type == "phone":
                    if not is_valid_us_phone_number(value):
                        error_dtypes.append(("phone", message))

    return error_dtypes


def show_dtype_error_message(error_dtypes: list) -> None:
    email_errors = [
        error_tuple[-1] for error_tuple in error_dtypes if error_tuple[0] == "email"
    ]
    phone_errors = [
        error_tuple[-1] for error_tuple in error_dtypes if error_tuple[0] == "phone"
    ]

    if len(email_errors) != 0:
        st.error(
            "Please input valid email on these fields (example@example.com) :",
            icon="📧",
        )

        st.write("<ul>", unsafe_allow_html=True)
        for email_error in email_errors:
            st.write(f"<li>{email_error}</li>", unsafe_allow_html=True)
        st.write("</ul>", unsafe_allow_html=True)

    if len(phone_errors) != 0:
        st.error("Please input valid phone on these fields:", icon="📞")

        st.write("<ul>", unsafe_allow_html=True)
        for phone_error in phone_errors:
            st.write(f"<li>{phone_error}</li>", unsafe_allow_html=True)
        st.write("</ul>", unsafe_allow_html=True)


def multiselect_checkbox(message: str, options: list) -> list:

    def is_others(option):
        option_lower = option.lower()
        return option_lower == "other" or option_lower == "others"

    st.write(message)
    selected_values = []
    for option in options:
        if is_others(option):
            other_value = st.text_input(label="Other")
            selected_values.append(other_value)
        else:
            selected = st.checkbox(option)
            if selected:
                selected_values.append(option)
    selected_values = [val for val in selected_values if val != ""]
    return selected_values


def generate_min() -> datetime:
    return datetime.now() - timedelta(days=365 * 100)


def generate_max() -> datetime:
    return datetime.now() + timedelta(days=365 * 100)


def process_field(
    field: dict, field_functions: dict, option_fields: list, result: dict
):
    field_type = field.get("type", "text")
    field_name = field["field_name"]
    message = field["message"] if "message" in field.keys() else ""
    if field.get("required", False):
        message = f"*{message}"

    if field_type in field_functions:
        if field_type in option_fields:
            options = [] if "options" not in field.keys() else field["options"]
            if field_type == "radio":
                data = field_functions[field_type](message, options=options, index=None)
            else:
                data = field_functions[field_type](message, options=options)
        else:
            if field_type == "date":
                data = field_functions[field_type](
                    message,
                    min_value=generate_min(),
                    max_value=generate_max(),
                    value=None,
                )
            else:
                # text input
                data = field_functions[field_type](
                    message, key=field_name, placeholder=field.get("placeholder")
                )
        if field_type != "message":
            result[field_name] = data


def generate_form(
    config_data: dict, index: int, section_fields: list = None, section=None
) -> None:
    data = config_data[index]
    form_name = data["name"]

    fields = data["fields"] if section_fields is None else section_fields

    result = {}
    field_functions = {
        "message": st.write,
        "text": st.text_input,
        "number": st.number_input,
        "date": st.date_input,
        "check": st.checkbox,
        "select": st.selectbox,
        "multiselect": st.multiselect,
        "textarea": st.text_area,
        "toggle": st.toggle,
        "radio": st.radio,
        "multiselect-checkbox": multiselect_checkbox,
    }

    row_classes_dict = {}
    col_index = None
    for field in fields:
        row_class = field.get("row_class")
        if row_class:
            if row_class in row_classes_dict:
                row_classes_dict[row_class].append(field["field_name"])
            else:
                row_classes_dict[row_class] = [field["field_name"]]

    option_fields = ["select", "multiselect", "radio", "multiselect-checkbox"]

    st.subheader(form_name if section is None else f"Section {section}")

    for field in fields:
        row_class = field.get("row_class")

        if row_class:
            col_index = field["col"]
            len_cols = len(row_classes_dict[row_class])
            if col_index == 1:
                st.session_state["current_cols"] = st.columns(len_cols)
            with st.session_state["current_cols"][col_index - 1]:
                process_field(field, field_functions, option_fields, result)
        else:
            process_field(field, field_functions, option_fields, result)
    st.markdown(
        """
        <style>
            div[data-testid="column"] {
                width: fit-content !important;
                flex: unset;
            }
            div[data-testid="column"] * {
                width: fit-content !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # if section_fields is None it means the field_type is Full Form Intake
    if section_fields is None:

        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button(
                "Submit",
                disabled=(st.session_state.get("form_submitted", False)),
                type="primary",
            )
        with col2:
            cancel = st.form_submit_button("Cancel")

        if submitted:
            error_fields = validate_required(fields, result)
            error_dtypes = validate_dtype(fields, result)
            if (len(error_fields) == 0) & (len(error_dtypes) == 0):
                st.session_state["result"] = result
                st.session_state["form_submitted"] = True
                generate_report(fields, st.session_state.get("result"), form_name)
                st.rerun()
            else:
                if len(error_fields) != 0:
                    show_required_error_message(error_fields)
                if len(error_dtypes) != 0:
                    show_dtype_error_message(error_dtypes)

        if cancel:
            st.session_state.clear()
            st.rerun()

    # if section_fields is not None then the fill_type is Sections Intake
    else:
        col1, col2 = st.columns([1, 1])
        with col1:
            continue_btn = st.form_submit_button("Continue", type="primary")
        with col2:
            cancel_btn = st.form_submit_button("Cancel")

        if continue_btn:
            error_fields = validate_required(fields, result)
            error_dtypes = validate_dtype(fields, result)
            if (len(error_fields) == 0) & (len(error_dtypes) == 0):
                final_result = st.session_state.get("result", {})
                for key, val in result.items():
                    final_result[key] = val
                st.session_state["result"] = final_result

                current_section_index = st.session_state.get("current_section_index", 0)
                st.session_state["current_section_index"] = current_section_index + 1
                st.session_state["show_sidebar"] = True
                st.rerun()
            else:
                if len(error_fields) != 0:
                    show_required_error_message(error_fields)
                if len(error_dtypes) != 0:
                    show_dtype_error_message(error_dtypes)


def generate_field(
    field: dict, field_functions: dict, current_field_index: int
) -> None:
    with st.form("Form"):
        option_fields = ["select", "multiselect", "radio", "multiselect-checkbox"]
        field_type = field.get("type", "text")
        field_name = field["field_name"]
        specific_type = field.get("specific_type")
        message = field.get("message", field_name)
        required = field.get("required", False)
        assistant = st.chat_message("assistant", avatar=np.array(bot_avatar))
        if required:
            message = f"*{message}"
        if field_type in field_functions:
            options = field.get("options", [])
            if field_type == "date":
                with assistant:
                    data = field_functions[field_type](
                        message,
                        min_value=generate_min(),
                        max_value=generate_max(),
                        value=None,
                    )
            elif field_type in option_fields:
                with assistant:
                    if field_type == "radio":
                        data = field_functions[field_type](
                            message, options=options, index=None
                        )
                    else:
                        data = field_functions[field_type](message, options=options)
            else:
                with assistant:
                    data = field_functions[field_type](message)

        result = st.session_state.get("result", {})
        with assistant:
            submit_btn = st.form_submit_button("Continue")
        if submit_btn:
            if required and not data:
                assistant.error("Please fill the field")
            elif data and specific_type:
                if specific_type == "email" and not is_valid_email(data):
                    st.warning(
                        "Please input a valid email format (example@example.com)",
                        icon="📧",
                    )
                elif specific_type == "phone" and not is_valid_us_phone_number(data):
                    st.warning(
                        "Please input a valid phone number format (XXX-XXX-XXXX)",
                        icon="📞",
                    )
                else:
                    if field_type != "message":
                        result[field_name] = data
                    st.session_state["result"] = result
                    st.session_state["current_field_index"] = current_field_index + 1
                    st.rerun()
            else:
                if field_type != "message":
                    result[field_name] = data
                st.session_state["result"] = result
                st.session_state["current_field_index"] = current_field_index + 1
                st.rerun()


def show_sidebar() -> None:
    if st.session_state.get("show_sidebar", False) and st.session_state["show_sidebar"]:
        with st.sidebar:
            st.header("Data")
            result = st.session_state.get("result", {})
            for key, value in result.items():
                st.text(f"{key}: {value}")


def generate_fields(config_data: dict, index: int) -> None:
    data = config_data[index]
    form_name = data["name"]
    fields = data["fields"]

    field_functions = {
        "message": st.write,
        "text": st.text_input,
        "number": st.number_input,
        "date": st.date_input,
        "check": st.checkbox,
        "select": st.selectbox,
        "multiselect": st.multiselect,
        "textarea": st.text_area,
        "toggle": st.checkbox,  # Change to appropriate function
        "radio": st.radio,
        "multiselect-checkbox": multiselect_checkbox,
    }

    show_sidebar()

    current_field_index = st.session_state.get("current_field_index", 0)
    if current_field_index < len(fields):
        field = fields[current_field_index]
        generate_field(field, field_functions, current_field_index)
    else:
        st.markdown(
            """
        <style>
            section[data-testid="stSidebar"][aria-expanded="true"]{
                display: none;
            }
        </style>
        """,
            unsafe_allow_html=True,
        )

        with st.chat_message("assistant", avatar=np.array(bot_avatar)):
            show_confirm(
                in_form=False,
                fields=fields,
                form_name=form_name,
                result=st.session_state["result"],
            )


def show_confirm(in_form: bool, fields: list, result: dict, form_name: str) -> None:
    with st.container(border=not in_form):
        st.subheader("Data Report:")
        result = st.session_state["result"]
        for key, value in result.items():
            st.text(f"{key}: {value}")

        st.markdown(
            """
        <style>
            div[data-testid="column"] {
                width: fit-content !important;
                flex: unset;
            }
            div[data-testid="column"] * {
                width: fit-content !important;
            }
        </style>
        """,
            unsafe_allow_html=True,
        )
        st.warning("Are you sure want to submit?")
        col1, col2 = st.columns([1, 1])
        btn_type = st.button if not in_form else st.form_submit_button
        with col1:
            submitted = btn_type(
                "Submit",
                disabled=(st.session_state.get("form_submitted", False)),
                type="primary",
            )
        with col2:
            cancel = btn_type(
                "Cancel",
                disabled=(st.session_state.get("form_submitted", False)),
            )

        if submitted:
            st.session_state["form_submitted"] = True
            generate_report(fields, result, form_name)
            st.rerun()


def generate_section(config_data: dict, index: int, section) -> None:
    this_config = config_data.copy()
    data = this_config[index]

    form_name = data["name"]
    fields = data["fields"]

    section_fields = [
        field
        for field in fields
        if "section" in field.keys() and field["section"] == section
    ]
    this_config[index]["fields"] = section_fields

    generate_form(this_config, index, section_fields, section)


def generate_sections(config_data: dict, index: int) -> None:
    data = config_data[index]
    form_name = data["name"]
    fields = data["fields"]

    sections = sorted(
        set([field["section"] for field in fields if "section" in field.keys()])
    )

    if len(sections) != 0:

        show_sidebar()

        current_section_index = st.session_state.get("current_section_index", 0)
        if current_section_index < len(sections):
            section = sections[current_section_index]
            generate_section(config_data, index, section)
        else:
            st.markdown(
                """
            <style>
                section[data-testid="stSidebar"][aria-expanded="true"]{
                    display: none;
                }
            </style>
            """,
                unsafe_allow_html=True,
            )
            show_confirm(
                in_form=True,
                fields=fields,
                result=st.session_state["result"],
                form_name=form_name,
            )
    else:
        st.subheader("This form doesn't have Section Wise Intake")
        restart_btn = st.form_submit_button("Restart")
        if restart_btn:
            st.session_state.clear()
            st.rerun()


def send_email(html_content, send_type):
    # Email configuration
    sender_email = "ekounseken@gmail.com"
    receiver_email = "ekounseken@gmail.com"
    password = "pkyy jfsp xgzj ghbu"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587  # Use the appropriate port for your SMTP server

    # Create message container
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Email Subject"

    def attach():
        # Convert HTML content to PDF and attach it
        pdf_content = pdfkit.from_string(html_content, False)
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pdf_content)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", 'attachment; filename="attachment.pdf"')
        msg.attach(part)

    if send_type == "attach":
        attach()
    elif send_type == "body":
        msg.attach(MIMEText(html_content, "html"))
        attach()

    # Connect to SMTP server and send email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())


def generate_report(fields, result, form_name):

    open_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Data Report</title>
        <style>
        body {
            font-family: 'Roboto', sans-serif;
            padding: 30px;
        }
        .message {

        }
        .value {
            padding: 15px;
            background-color: #ebeef2;
            border-radius: 5px;
        }
        
        
        
        .message-only {
            margin-bottom: 5px;
            margin-top: 50px;
            font-style: italic;
        }
        
        
        
        </style>
    </head>
    <body>
    <form>
    """

    open_html += f"""
    <h1>{form_name}</h1>
    """

    container_open = f"""
    <div class='container'>
    """
    container_close = "</div>"
    for field in fields:
        field_name = field["field_name"]
        field_type = field["type"]
        message = field.get("message")
        row_class = field.get("row_class")
        col = field.get("col")

        item_div = f"""
        <div class = 'item {'message-only' if field_type == "message" else ''}'>
        """

        html_message = f"""
            <p class='message'>{message}:</p>
            """

        item_div += html_message

        if field_type == "multiselect-checkbox":
            options = field.get("options", [])
            values = result[field_name]
            lower_options = [option.lower() for option in options]
            other_val = "".join([value for value in values if value not in options])

            for i, option in enumerate(options):

                html_element = f"""
                <input type='checkbox' {'checked' if option in values else ''} id='checkbox{option.replace(" ", "")}' name='checkbox{option.replace(" ", "")}'>
                <label for='checkbox{option.replace(" ", "")}'>{option}</label>
                """
                item_div += html_element
                # open_html += html_element
            if ("other" in lower_options or "others" in lower_options) and other_val:
                other_html = f"""
                <p>Other:</p>
                <p class='value''>{other_val}</p>
                """
                item_div += other_html
        elif field_type == "radio":
            options = field.get("options", [])
            value = result[field_name]

            for i, option in enumerate(options):
                html_element = f"""
                <input type='radio' {'checked' if option == value else ''} id='radio{option.replace(" ", "")}' name='radio{option.replace(" ", "")}'>
                <label for='radio{option.replace(" ", "")}'>{option}</label>
                """
                # open_html += html_element
                item_div += html_element
        elif field_type != "message":
            value = result[field_name]
            html_element = f"""
            <p class='value'>{value if value else "NA"}</p>
            """
            item_div += html_element
        item_div += "</div>"
        container_open += item_div

    container = container_open + container_close
    open_html += container

    closing_html = """
    </form>
    </body>
    </html>
    """

    final_html = open_html + closing_html

    with open("output.html", "w") as file:
        file.write(final_html)
    pdfkit.from_string(final_html, "output.pdf")

    send_type = st.session_state.get("send_type", "body")
    send_email(final_html, send_type)
