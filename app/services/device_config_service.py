import os
from models.device_config import DeviceConfig
import time

CONFIG_DIR = "configs"


class DeviceConfigService:

    def save(
        self,
        db,
        device,
        content: str,
        storage: str,
        user_id: int,
        comment: str | None = None
    ):
        # Если storage "blob" или "db", сохраняем в базу
        if storage in ("blob", "db"):
            cfg = DeviceConfig(
                device_id=device.id,
                storage="blob",
                config_blob=content.encode("utf-8"),
                created_by=user_id,
                comment=comment
            )

        # Если storage "file", сохраняем в файл
        elif storage == "file":
            os.makedirs(CONFIG_DIR, exist_ok=True)

            filename = f"{device.id}_{int(time.time())}.cfg"
            path = os.path.join(CONFIG_DIR, filename)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            cfg = DeviceConfig(
                device_id=device.id,
                storage="file",
                file_path=path,
                created_by=user_id,
                comment=comment
            )

        # Любой другой тип кидает исключение
        else:
            raise ValueError(f"Invalid storage type: {storage}")

        db.add(cfg)
        db.commit()
        return cfg