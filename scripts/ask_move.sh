#!/bin/bash

TARGET_DIR="$HOME/good_line_bot"
HOME_DIR="$HOME"

# 確保目標資料夾存在
mkdir -p "$TARGET_DIR"

# 遍歷下載下來的專案內容 (包含檔案與資料夾)
# 使用 shopt -s dotglob 來確保隱藏檔案 (如 .gitignore, .agents) 也會被抓到
shopt -s dotglob
for item in ./duck/*; do
    # 取出檔名或資料夾名稱
    basename=$(basename "$item")
    
    # 略過不需要部署的檔案
    if [[ "$basename" == ".agent" || "$basename" == ".agents" || "$basename" == ".gitignore" || "$basename" == "README.md" || "$basename" == "requirements.txt" || "$basename" == ".git" ]]; then
        continue
    fi
    
    if [ "$basename" = "scripts" ]; then
        # 遇到 scripts 資料夾，將裡面的 .sh 移到 ~ 底下
        read -p "Move scripts (*.sh) to $HOME_DIR/? (y/n): " answer
        case ${answer:0:1} in
            n|N ) 
                echo "⏭️ Skipped scripts" 
            ;;
            * )
                cp -r "$item"/*.sh "$HOME_DIR/"
                chmod +x "$HOME_DIR"/*.sh
                echo "✅ Moved and chmod scripts to $HOME_DIR/"
            ;;
        esac
    else
        # 其他 Python 檔案與 core, services, utils 資料夾移到 good_line_bot/
        read -p "Move '$basename' to $TARGET_DIR/? (y/n): " answer
        case ${answer:0:1} in
            n|N ) 
                echo "⏭️ Skipped $basename" 
            ;;
            * )
                # 使用 cp -R 覆蓋以支援資料夾結構的更新
                cp -R "$item" "$TARGET_DIR/"
                echo "✅ Moved $basename to $TARGET_DIR/"
            ;;
        esac
    fi
done
