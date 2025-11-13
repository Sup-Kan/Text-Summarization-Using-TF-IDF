# !/bin/bash
# create_gitkeep.sh

# Tạo .gitkeep cho các thư mục rỗng
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch logs/.gitkeep
touch logs/preprocessing/.gitkeep
touch models/.gitkeep
touch models/vncorenlp/.gitkeep
touch models/vncorenlp/stopwords/.gitkeep

echo "✓ Created .gitkeep files"