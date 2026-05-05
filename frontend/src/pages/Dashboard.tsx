import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="dashboard">
      <nav>
        <button onClick={handleLogout}>Sair</button>
      </nav>
      <h1>Dashboard</h1>
      <p>Bem-vindo{user?.username ? `, ${user.username}` : ''}!</p>
      {user?.profile && <p>Perfil: {user.profile}</p>}
      <p>Área autenticada — conteúdo em construção.</p>
    </div>
  )
}
