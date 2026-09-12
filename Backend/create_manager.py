from app.auth.password import hash_password
from app.core.mongodb import get_database


def main():

    db = get_database()

    username = "manager"
    password = "manager123"

    existing = db.managers.find_one(
        {
            "username": username
        }
    )

    if existing:

        print(
            f"Manager '{username}' already exists."
        )

        return


    manager = {
        "name": "Plant Manager",
        "username": username,
        "password_hash": hash_password(
            password
        ),
        "role": "manager",
    }


    result = db.managers.insert_one(
        manager
    )


    print(
        "Manager created successfully."
    )

    print(
        "ID:",
        result.inserted_id
    )

    print(
        "Username:",
        username
    )

    print(
        "Password:",
        password
    )


if __name__ == "__main__":
    main()