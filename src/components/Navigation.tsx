
'use client'

import { Navbar, Nav, NavDropdown, Container, Button } from 'react-bootstrap'
import { useAuth } from '@/app/providers'
import { useRouter } from 'next/navigation'
import Image from 'next/image'

export default function Navigation() {
  const { user, logout } = useAuth()
  const router = useRouter()

  const handleLogout = async () => {
    await logout()
    router.push('/')
  }

  if (!user) return null

  return (
    <Navbar bg="dark" variant="dark" expand="lg" fixed="top">
      <Container>
        <Navbar.Brand href="/" className="d-flex align-items-center">
          <Image 
            src="/f-ai-logo.png" 
            alt="F-AI Logo" 
            width={32} 
            height={32} 
            className="me-2"
          />
          F-AI Accountant
        </Navbar.Brand>
        
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link href="/dashboard">Dashboard</Nav.Link>
            <Nav.Link href="/ai-accounting">AI Accounting</Nav.Link>
            <Nav.Link href="/bank-reconciliation">Bank Reconciliation</Nav.Link>
            <Nav.Link href="/file-interaction">File Interaction</Nav.Link>
            
            <NavDropdown title="Portals" id="portals-dropdown">
              <NavDropdown.Item href="/portals/invoice">Invoice Portal</NavDropdown.Item>
              <NavDropdown.Item href="/portals/inventory">Inventory Portal</NavDropdown.Item>
              <NavDropdown.Item href="/portals/gst">GST Portal</NavDropdown.Item>
              <NavDropdown.Item href="/portals/audit">Audit Portal</NavDropdown.Item>
              <NavDropdown.Item href="/portals/reports">Reports Portal</NavDropdown.Item>
              <NavDropdown.Item href="/portals/ai-insights">AI Insights Portal</NavDropdown.Item>
            </NavDropdown>
            
            {user.role === 'admin' && (
              <Nav.Link href="/admin">Admin</Nav.Link>
            )}
          </Nav>
          
          <Nav>
            <NavDropdown title={user.first_name || user.username} id="user-dropdown">
              <NavDropdown.Item href="/profile">Profile</NavDropdown.Item>
              <NavDropdown.Divider />
              <NavDropdown.Item onClick={handleLogout}>Logout</NavDropdown.Item>
            </NavDropdown>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  )
}
