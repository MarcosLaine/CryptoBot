#!/usr/bin/env python3
"""
Script para visualizar usuários cadastrados no CryptoBot
"""
import sqlite3
from datetime import datetime

DB_PATH = 'cryptobot.db'

def view_users():
    """Lista todos os usuários cadastrados no sistema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Buscar todos os usuários
        cursor.execute('''
            SELECT id, username, created_at 
            FROM users 
            ORDER BY id
        ''')
        users = cursor.fetchall()
        
        if not users:
            print("\n❌ Nenhum usuário cadastrado no sistema.\n")
            conn.close()
            return
        
        print("\n" + "="*70)
        print("👥 USUÁRIOS CADASTRADOS NO CRYPTOBOT")
        print("="*70)
        
        for user in users:
            user_id, username, created_at = user
            print(f"\n📋 ID: {user_id}")
            print(f"👤 Username: {username}")
            print(f"📅 Cadastrado em: {created_at}")
            
            # Verificar se tem API keys configuradas
            cursor.execute('SELECT COUNT(*) FROM api_keys WHERE user_id = ?', (user_id,))
            has_api_keys = cursor.fetchone()[0] > 0
            print(f"🔑 API Keys: {'✅ Configuradas' if has_api_keys else '❌ Não configuradas'}")
            
            # Verificar se o bot está rodando
            cursor.execute('SELECT is_running FROM bot_status WHERE user_id = ?', (user_id,))
            bot_status = cursor.fetchone()
            is_running = bot_status[0] if bot_status else 0
            print(f"🤖 Bot Status: {'✅ Rodando' if is_running else '⏸️  Parado'}")
            
            print("-" * 70)
        
        print(f"\n📊 Total de usuários: {len(users)}\n")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"\n❌ Erro ao acessar o banco de dados: {e}\n")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}\n")

def reset_password(username, new_password):
    """
    Redefine a senha de um usuário
    
    Args:
        username: Nome do usuário
        new_password: Nova senha
    """
    from werkzeug.security import generate_password_hash
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se o usuário existe
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"\n❌ Usuário '{username}' não encontrado.\n")
            conn.close()
            return
        
        # Gerar hash da nova senha
        password_hash = generate_password_hash(new_password)
        
        # Atualizar senha
        cursor.execute(
            'UPDATE users SET password_hash = ? WHERE username = ?',
            (password_hash, username)
        )
        conn.commit()
        conn.close()
        
        print(f"\n✅ Senha do usuário '{username}' redefinida com sucesso!\n")
        
    except Exception as e:
        print(f"\n❌ Erro ao redefinir senha: {e}\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset" and len(sys.argv) == 4:
            # python view_users.py reset <username> <nova_senha>
            username = sys.argv[2]
            new_password = sys.argv[3]
            reset_password(username, new_password)
        else:
            print("\n❌ Uso incorreto!")
            print("\nPara visualizar usuários:")
            print("  python view_users.py")
            print("\nPara redefinir senha:")
            print("  python view_users.py reset <username> <nova_senha>\n")
    else:
        # Visualizar usuários
        view_users()

