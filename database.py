# coding: utf8

import sqlite3
from datetime import datetime


def build_article_dictionary(row):
    return {
        "id": row[0], "titre": row[1], "identifiant": row[2],
        "auteur": row[3], "date_publication": row[4], "paragraphe": row[5]
    }


class Database:
    def __init__(self):
        self.connection = None

    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect('db/db.db')
            # Création de la BD
            # cursor = self.connection.cursor()
            # f = open('db/db.sql','r')
            # sql = f.read()
            # cursor.executescript(sql)
        return self.connection

    def disconnect(self):
        if self.connection is not None:
            self.connection.close()
    

    def create_user(self, username, email, salt, hashed_password):
        connection = self.get_connection()
        connection.execute(("insert into users(utilisateur, email, salt, hash)"
                            " values(?, ?, ?, ?)"), (username, email, salt,
                                                     hashed_password))
        connection.commit()

    def get_user_login_info(self, username):
        cursor = self.get_connection().cursor()
        cursor.execute(("select salt, hash from users where utilisateur=?"),
                       (username,))
        user = cursor.fetchone()
        if user is None:
            return None
        else:
            return user[0], user[1]

    def save_session(self, id_session, username):
        connection = self.get_connection()
        connection.execute(("insert into sessions(id_session, utilisateur) "
                            "values(?, ?)"), (id_session, username))
        connection.commit()

    def delete_session(self, id_session):
        connection = self.get_connection()
        connection.execute(("delete from sessions where id_session=?"),
                           (id_session,))
        connection.commit()

    def get_session(self, id_session):
        cursor = self.get_connection().cursor()
        cursor.execute(("select utilisateur from sessions where id_session=?"),
                       (id_session,))
        data = cursor.fetchone()
        if data is None:
            return None
        else:
            return data[0]
    
    def get_articles(self):
        cursor = self.get_connection().cursor()
        cursor.execute("select * from article")
        articles = cursor.fetchall()
        return [build_article_dictionary(each) for each in articles]

    def get_last_articles(self):
        cursor = self.get_connection().cursor()
        cursor.execute(
                "select * from article" +
                " where date_publication <= ?" +
                "order by date_publication DESC limit 5",
                (datetime.now().strftime("%Y-%m-%d"),)
             )
        articles = cursor.fetchall()
        return [build_article_dictionary(each) for each in articles]

    def get_article_rechercher(self, mot):
        mot = "%" + mot + "%"
        cursor = self.get_connection().cursor()
        cursor.execute(
            "select * from article where titre like ? OR paragraphe like ? ",
            (mot, mot))
        articles = cursor.fetchall()
        return [build_article_dictionary(each) for each in articles]

    def get_article(self, identifier):
        cursor = self.get_connection().cursor()
        cursor.execute(
            "select * from article where identifiant = ?", (identifier,)
        )
        article = cursor.fetchone()
        if article is None:
            return None
        else:
            return build_article_dictionary(article)

    def insert_article(self, titre, id, auteur, date_publication, paragraphe):
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            ("insert into article(titre, identifiant, auteur, date_publication, paragraphe)"
                "values(?, ?, ?, ?, ?)"),
            (titre, id, auteur, date_publication, paragraphe)
            )
        connection.commit()

    def update_article(self, titre, identifiant, paragraphe):
        print titre
        print paragraphe
        print identifiant
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "update article SET titre=?, paragraphe = ? where identifiant = ?",
            (titre, paragraphe, identifiant)
            )
        connection.commit()
