from datetime import datetime

from sqlalchemy import text

from core.enums import ChatTypeEnum
from db.session import get_session
from utils.utils import pwd_context


async def init_data() -> None:
    session = await get_session().__anext__()
    try:
        await session.execute(
            text(
                "TRUNCATE TABLE messages, chats_participants, chats, users RESTART IDENTITY CASCADE"
            )
        )

        users = [
            {"name": "Иван Петров", "email": "ivan@example.com", "password": "123"},
            {"name": "Мария Сидорова", "email": "maria@example.com", "password": "123"},
            {"name": "Алексей Иванов", "email": "alex@example.com", "password": "123"},
            {"name": "Елена Смирнова", "email": "elena@example.com", "password": "123"},
            {
                "name": "Дмитрий Кузнецов",
                "email": "dmitry@example.com",
                "password": "123",
            },
        ]

        await session.execute(
            text("""
            INSERT INTO users (name, email, hashed_password) 
            VALUES 
                (:name1, :email1, :password1),
                (:name2, :email2, :password2),
                (:name3, :email3, :password3),
                (:name4, :email4, :password4),
                (:name5, :email5, :password5)
            """),
            {
                "name1": users[0]["name"],
                "email1": users[0]["email"],
                "password1": pwd_context.hash(users[0]["password"]),
                "name2": users[1]["name"],
                "email2": users[1]["email"],
                "password2": pwd_context.hash(users[1]["password"]),
                "name3": users[2]["name"],
                "email3": users[2]["email"],
                "password3": pwd_context.hash(users[2]["password"]),
                "name4": users[3]["name"],
                "email4": users[3]["email"],
                "password4": pwd_context.hash(users[3]["password"]),
                "name5": users[4]["name"],
                "email5": users[4]["email"],
                "password5": pwd_context.hash(users[4]["password"]),
            },
        )

        chats = [
            {"name": "Приватный чат 1-2", "type": ChatTypeEnum.private.name},
            {"name": "Приватный чат 3-4", "type": ChatTypeEnum.private.name},
            {"name": "Группа поддержки", "type": ChatTypeEnum.public.name},
            {"name": "Командный чат", "type": ChatTypeEnum.public.name},
            {"name": "Приватный чат 2-5", "type": ChatTypeEnum.public.name},
        ]

        await session.execute(
            text("""
            INSERT INTO chats (name, chat_type) 
            VALUES 
                (:name1, :type1),
                (:name2, :type2),
                (:name3, :type3),
                (:name4, :type4),
                (:name5, :type5)
            """),
            {
                "name1": chats[0]["name"],
                "type1": chats[0]["type"],
                "name2": chats[1]["name"],
                "type2": chats[1]["type"],
                "name3": chats[2]["name"],
                "type3": chats[2]["type"],
                "name4": chats[3]["name"],
                "type4": chats[3]["type"],
                "name5": chats[4]["name"],
                "type5": chats[4]["type"],
            },
        )

        participants = [
            (1, 1),
            (1, 2),
            (2, 3),
            (2, 4),
            (3, 1),
            (3, 2),
            (3, 3),
            (3, 4),
            (3, 5),
            (4, 2),
            (4, 3),
            (4, 5),
            (5, 2),
            (5, 5),
        ]

        await session.execute(
            text("""
            INSERT INTO chats_participants (chat_id, participant_id) 
            VALUES 
                (:pair1_1, :pair1_2),
                (:pair2_1, :pair2_2),
                (:pair3_1, :pair3_2),
                (:pair4_1, :pair4_2),
                (:pair5_1, :pair5_2),
                (:pair6_1, :pair6_2),
                (:pair7_1, :pair7_2),
                (:pair8_1, :pair8_2),
                (:pair9_1, :pair9_2),
                (:pair10_1, :pair10_2),
                (:pair11_1, :pair11_2),
                (:pair12_1, :pair12_2)
            """),
            {
                "pair1_1": participants[0][0],
                "pair1_2": participants[0][1],
                "pair2_1": participants[1][0],
                "pair2_2": participants[1][1],
                "pair3_1": participants[2][0],
                "pair3_2": participants[2][1],
                "pair4_1": participants[3][0],
                "pair4_2": participants[3][1],
                "pair5_1": participants[4][0],
                "pair5_2": participants[4][1],
                "pair6_1": participants[5][0],
                "pair6_2": participants[5][1],
                "pair7_1": participants[6][0],
                "pair7_2": participants[6][1],
                "pair8_1": participants[7][0],
                "pair8_2": participants[7][1],
                "pair9_1": participants[8][0],
                "pair9_2": participants[8][1],
                "pair10_1": participants[9][0],
                "pair10_2": participants[9][1],
                "pair11_1": participants[10][0],
                "pair11_2": participants[10][1],
                "pair12_1": participants[11][0],
                "pair12_2": participants[11][1],
            },
        )

        messages = [
            (1, 1, "Привет, Мария!", True, datetime.now()),
            (1, 2, "Здравствуй, Иван!", True, datetime.now()),
            (1, 1, "Как дела?", False, datetime.now()),
            (2, 3, "Елена, привет!", True, datetime.now()),
            (2, 4, "Привет, Алексей!", True, datetime.now()),
            (3, 1, "Всем добрый день!", True, datetime.now()),
            (3, 3, "Есть вопросы по проекту", True, datetime.now()),
            (3, 5, "Я могу помочь", False, datetime.now()),
            (4, 2, "Кто готов к митингу?", True, datetime.now()),
            (4, 5, "Я готов", True, datetime.now()),
            (5, 2, "Дмитрий, документы готовы?", False, datetime.now()),
            (5, 5, "Да, отправляю вам", False, datetime.now()),
        ]

        params = {}
        values = []
        for i, (chat_id, sender_id, msg_text, was_read, created_at) in enumerate(
            messages, 1
        ):
            params.update(
                {
                    f"msg{i}_chat": chat_id,
                    f"msg{i}_sender": sender_id,
                    f"msg{i}_text": msg_text,
                    f"msg{i}_read": was_read,
                    f"msg{i}_time": created_at,
                }
            )
            values.append(
                f"(:msg{i}_chat, :msg{i}_sender, :msg{i}_text, :msg{i}_read, :msg{i}_time)"
            )

        query = text(f"""
            INSERT INTO messages (chat_id, sender_id, text, was_read, created_at)
            VALUES {",".join(values)}
        """)

        await session.execute(query, params)

        await session.commit()
        print("✅ Тестовые данные успешно созданы!")

    except Exception as e:
        await session.rollback()
        print(f"❌ Ошибка: {e}")
        raise
    finally:
        await session.close()
