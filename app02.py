import openai
import os
import sys
import threading
from dotenv import load_dotenv
# import codecs
import datetime

load_dotenv()


def get_user_choice():
    user_choice = input_with_unicode("\n답변 내용이 도움이 되셨나요?\n입력: 대화를 계속하시려면 (c), 그만하시려면 (f), 담당자 연결을 원하시면 (r): ")
    return user_choice.lower()

def handle_user_choice(user_choice, current_time, conversation_history):
    if user_choice == "c":
        return True
    elif user_choice == "f":
        print("이용해주셔서 감사합니다.")
        log_conversation_end(user_choice, current_time)
        return False
    elif user_choice == "r":
        print("담당자가 연락드릴 때까지 잠시 기다려 주세요. 채팅 대화는 중단합니다.")
        log_conversation_end(user_choice, current_time)
        return False
    else:
        print("잘못된 입력입니다. 계속합니다.")
        return True



#로그용
def log_conversation_end(choice, current_time):
    with open("conversation_history02.log", "a", encoding="utf-8") as f:
        f.write(f"> {choice} Conversation ended at {current_time}\n")
def log_conversation_start(current_time):
    with open("conversation_history02.log", "a", encoding="utf-8") as f:
        f.write(f"\nConversation started at {current_time}\n")


def input_with_unicode(prompt):
    print(prompt, end="")
    sys.stdout.flush()
    return sys.stdin.buffer.readline().strip().decode("utf-8", errors="replace")

def log_to_file(entry):
    with open("conversation_history02.log", "a", encoding="utf-8") as f:
        f.write(f"{entry['role'].capitalize()}: {entry['content']}\n")

def call_gpt_with_timeout(conversation_history, timeout):
    result = [None]

    def call_gpt_thread():
        result[0] = call_gpt(conversation_history)

    gpt_thread = threading.Thread(target=call_gpt_thread)
    gpt_thread.start()
    gpt_thread.join(timeout)

    return result[0]

def call_gpt(conversation_history):
    prompt = "You are an in-house assistive AI chatbot that provides helpful answers to users who need help in the PC field. Create a completion that provides a solution to a user inquiry in Korean(tokens 1000 or less). The following is a conversation with an AI assistant.\n\n"

    for message in conversation_history:
        role = message["role"]
        content = message["content"]
        prompt += f"{role.capitalize()}: {content}\n"

    prompt += "Assistant:"

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=2000,
        n=1,
        stop=None,
        temperature=0.5,
    )

    return response.choices[0].text.strip()

def main():
    openai.api_key = os.getenv("OPENAI_API_KEY")

    print("환영합니다 GPT 챗봇입니다! PC서비스나 정보보안 관련 문의 처리를 도와드리고 있습니다.\n*주의사항: 여러가지 문제를 동시에 겪고 계시면 순서대로 한 번에 하나씩의 문의를 해주세요. 챗봇으로 해결되지 않은 문제는 담당자가 도와드리겠습니다(•v•)*")
    conversation_history = []

    # 대화 시작시 날짜 시간 로그 기록
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_conversation_start(current_time)

    while True:
        user_input = input_with_unicode("\n문의 내용을 입력해 주세요: ")

        if len(conversation_history) >= 4:
            conversation_history = conversation_history[:2] + conversation_history[-2:]

        user_entry = {"role": "user", "content": user_input}
        conversation_history.append(user_entry)
        log_to_file(user_entry)

        print("답변을 생성중입니다...")
        gpt_response = call_gpt_with_timeout(conversation_history, timeout=60)

        if gpt_response is None:
            print("...GPT가 답변을 생성하는 시간이 오래 걸렸습니다. 다시 시작중...")
            continue

        print(f"\nGPT-3 Response: {gpt_response}")

        assistant_entry = {"role": "assistant", "content": gpt_response}
        conversation_history.append(assistant_entry)
        log_to_file(assistant_entry)

        # (C)ontinue/(F)inish/(R)epresentative
        user_choice = get_user_choice()
        if not handle_user_choice(user_choice, current_time, conversation_history):
            break

if __name__ == "__main__":
    main()
