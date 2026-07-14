from src.load.snowflake_loader import get_snowflake_connection

try:
    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA(), "
        "CURRENT_ACCOUNT(), CURRENT_ORGANIZATION_NAME(), CURRENT_REGION()"
    )
    print(cur.fetchone())
    cur.close()
    conn.close()
except Exception as exc:
    message = str(exc)
    print("Connection failed:", message)
    if "404" in message:
        print(
            "\n404 usually means SNOWFLAKE_ACCOUNT is wrong.\n"
            "In Snowsight: Admin -> Accounts -> copy 'Account identifier' exactly.\n"
            "Common formats:\n"
            "  orgname-accountname   (e.g. myorg-myaccount)\n"
            "  locator.region.cloud  (e.g. xy12345.us-east-1.aws)\n"
            "Do NOT include https:// or .snowflakecomputing.com"
        )
