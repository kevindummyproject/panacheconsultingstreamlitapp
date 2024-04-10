import streamlit as st
import numpy as np
import json
from functions import *
from PIL import Image
import requests


def main():
    def get_all_countries():
        try:
            url = "https://restcountries.com/v3.1/all"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                countries = [country["name"]["common"] for country in data]
                return countries
            else:
                print("Failed to fetch data")
                return None
        except:
            return []

    # Example usage
    if "countries" not in st.session_state.keys():
        st.session_state["countries"] = get_all_countries()

    # bot_avatar = Image.open("./assets/bot-avatar.png")
    bot_avatar = Image.open("./assets/Bot.png")

    config_json = "config.json"
    with open(config_json, "r") as config_file:
        config_data = json.load(config_file)
    st.image("./assets/logo.png", width=300)

    title = config_data.get("title", "Panache Consulting")
    st.session_state["send_type"] = config_data.get("send_type", "body")

    st.title(title)

    greeting = get_local_time_greeting()
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {"role": "assistant", "content": f"Hello! {greeting}"},
        ]

    for message in st.session_state.messages:
        with st.chat_message(
            message["role"],
            avatar=np.array(bot_avatar) if message["role"] == "assistant" else None,
        ):
            st.write(message["content"])

    form_assistant = st.chat_message("assistant", avatar=np.array(bot_avatar))

    if "form_disabled" not in st.session_state.keys():
        st.session_state["form_disabled"] = False

    form_options = [data["name"] for data in config_data["data"]]
    form_name = form_assistant.selectbox(
        "Choose form you want to fill:",
        index=None,
        options=form_options,
        placeholder="Choose",
        disabled=st.session_state["form_disabled"],
    )

    if "form_chosen" not in st.session_state.keys():
        st.session_state["form_chosen"] = False
        form_name = None

    if form_name is not None:
        st.session_state["form_chosen"] = True
        st.session_state["form_index"] = form_options.index(form_name)

    if (st.session_state.get("form_chosen", False)) & (form_name is not None):
        type_assistant = st.chat_message("assistant", avatar=np.array(bot_avatar))

        fill_type = type_assistant.radio(
            "Which type do you want to choose",
            options=["Full Form Intake", "Section Wise Intake", "Field Wise Intake"],
            index=None,
            disabled="fill_type" in st.session_state.keys(),
        )

        if fill_type is not None:
            execute_btn = type_assistant.button(
                "Start", disabled="fill_type" in st.session_state.keys()
            )

            if execute_btn:
                st.session_state["form_disabled"] = True
                st.session_state["fill_type"] = fill_type
                st.rerun()

    if st.session_state.get("fill_type", False):
        fill_type = st.session_state["fill_type"]
        if fill_type == "Full Form Intake":
            with st.chat_message("assistant", avatar=np.array(bot_avatar)):
                with st.form("form"):
                    generate_form(config_data["data"], st.session_state["form_index"])

                    if st.session_state.get("result"):
                        st.write(st.session_state["result"])

            if st.session_state.get("form_submitted", False):
                st.chat_message("assistant", avatar=np.array(bot_avatar)).write(
                    "Thank you"
                )
        elif fill_type == "Field Wise Intake":
            st.session_state["show_sidebar"] = True
            generate_fields(config_data["data"], st.session_state["form_index"])
        elif fill_type == "Section Wise Intake":
            with st.chat_message("assistant", avatar=np.array(bot_avatar)):
                with st.form("form"):
                    generate_sections(
                        config_data["data"], st.session_state["form_index"]
                    )

    if st.session_state.get("form_submitted", False):
        st.success("Thank You! Your data have been sent!", icon="✅")


if __name__ == "__main__":
    main()
