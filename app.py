from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = "recipes.db"

# DB接続関数
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# DB初期化（初回起動時）
def init_db():
    if not os.path.exists(DB_PATH):
        conn = get_db_connection()
        with open("sql/create.sql", "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

# 動作確認用
@app.route("/")
def index():
    return jsonify({"message": "Recipe API is running"}), 200

# POST /recipes - 新規作成
@app.route("/recipes", methods=["POST"])
def create_recipe():
    data = request.get_json()
    required_fields = ["title", "making_time", "serves", "ingredients", "cost"]

    if not data or not all(field in data and data[field] for field in required_fields):
        return jsonify({
            "message": "Recipe creation failed!",
            "required": "title, making_time, serves, ingredients, cost"
        }), 200

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO recipes (title, making_time, serves, ingredients, cost, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["title"],
        data["making_time"],
        data["serves"],
        data["ingredients"],
        data["cost"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()

    recipe_id = cur.lastrowid
    cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    recipe = dict(cur.fetchone())
    conn.close()

    return jsonify({
        "message": "Recipe successfully created!",
        "recipe": [recipe]
    }), 200

# GET /recipes - 一覧取得
@app.route("/recipes", methods=["GET"])
def get_recipes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, making_time, serves, ingredients, cost FROM recipes")
    recipes = [dict(row) for row in cur.fetchall()]
    conn.close()

    return jsonify({"recipes": recipes}), 200

# GET /recipes/<id> - ID指定取得
@app.route("/recipes/<int:recipe_id>", methods=["GET"])
def get_recipe_by_id(recipe_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, making_time, serves, ingredients, cost FROM recipes WHERE id = ?", (recipe_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return jsonify({
            "message": "Recipe details by id",
            "recipe": [dict(row)]
        }), 200
    else:
        return jsonify({
            "message": "No Recipe found"
        }), 200

# PATCH /recipes/<id> - 更新
@app.route("/recipes/<int:recipe_id>", methods=["PATCH"])
def update_recipe(recipe_id):
    data = request.get_json()
    required_fields = ["title", "making_time", "serves", "ingredients", "cost"]

    if not data or not all(field in data and data[field] for field in required_fields):
        return jsonify({
            "message": "Recipe update failed!",
            "required": "title, making_time, serves, ingredients, cost"
        }), 200

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"message": "No Recipe found"}), 200

    cur.execute("""
        UPDATE recipes
        SET title = ?, making_time = ?, serves = ?, ingredients = ?, cost = ?, updated_at = ?
        WHERE id = ?
    """, (
        data["title"],
        data["making_time"],
        data["serves"],
        data["ingredients"],
        data["cost"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        recipe_id
    ))
    conn.commit()

    cur.execute("SELECT id, title, making_time, serves, ingredients, cost FROM recipes WHERE id = ?", (recipe_id,))
    updated_recipe = dict(cur.fetchone())
    conn.close()

    return jsonify({
        "message": "Recipe successfully updated!",
        "recipe": [updated_recipe]
    }), 200

# DELETE /recipes/<id> - 削除
@app.route("/recipes/<int:recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"message": "No Recipe found"}), 200

    cur.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Recipe successfully removed!"}), 200

# アプリ起動
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)