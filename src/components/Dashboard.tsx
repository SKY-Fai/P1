
'use client'

import { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Button } from 'react-bootstrap'
import Navigation from './Navigation'
import { useAuth } from '@/app/providers'

interface DashboardStats {
  total_files: number
  processed_files: number
  pending_files: number
  total_invoices: number
  total_inventory_items: number
}

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      const response = await fetch('/api/dashboard-stats')
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Navigation />
      <Container fluid className="pt-5 mt-3">
        <Row>
          <Col>
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h1>Welcome, {user?.first_name || user?.username}!</h1>
              <small className="text-muted">F-AI Accountant Dashboard</small>
            </div>
          </Col>
        </Row>

        {/* Statistics Cards */}
        <Row className="mb-4">
          <Col lg={3} md={6} className="mb-3">
            <Card className="dashboard-card h-100">
              <Card.Body>
                <div className="d-flex justify-content-between">
                  <div>
                    <h6 className="card-title text-muted">Total Files</h6>
                    <h3 className="mb-0">{loading ? '...' : stats?.total_files || 0}</h3>
                  </div>
                  <div className="text-primary">
                    <i className="fas fa-file-alt fa-2x"></i>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col lg={3} md={6} className="mb-3">
            <Card className="dashboard-card h-100">
              <Card.Body>
                <div className="d-flex justify-content-between">
                  <div>
                    <h6 className="card-title text-muted">Processed Files</h6>
                    <h3 className="mb-0">{loading ? '...' : stats?.processed_files || 0}</h3>
                  </div>
                  <div className="text-success">
                    <i className="fas fa-check-circle fa-2x"></i>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col lg={3} md={6} className="mb-3">
            <Card className="dashboard-card h-100">
              <Card.Body>
                <div className="d-flex justify-content-between">
                  <div>
                    <h6 className="card-title text-muted">Pending Files</h6>
                    <h3 className="mb-0">{loading ? '...' : stats?.pending_files || 0}</h3>
                  </div>
                  <div className="text-warning">
                    <i className="fas fa-clock fa-2x"></i>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col lg={3} md={6} className="mb-3">
            <Card className="dashboard-card h-100">
              <Card.Body>
                <div className="d-flex justify-content-between">
                  <div>
                    <h6 className="card-title text-muted">Total Invoices</h6>
                    <h3 className="mb-0">{loading ? '...' : stats?.total_invoices || 0}</h3>
                  </div>
                  <div className="text-info">
                    <i className="fas fa-receipt fa-2x"></i>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Quick Actions */}
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h5 className="mb-0">Quick Actions</h5>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col lg={4} md={6} className="mb-3">
                    <Card className="dashboard-card h-100">
                      <Card.Body className="text-center">
                        <i className="fas fa-robot fa-3x text-primary mb-3"></i>
                        <h5>AI Accounting</h5>
                        <p className="text-muted">Automated accounting with AI-powered processing</p>
                        <Button variant="primary" href="/ai-accounting">
                          Access AI Accounting
                        </Button>
                      </Card.Body>
                    </Card>
                  </Col>

                  <Col lg={4} md={6} className="mb-3">
                    <Card className="dashboard-card h-100">
                      <Card.Body className="text-center">
                        <i className="fas fa-university fa-3x text-success mb-3"></i>
                        <h5>Bank Reconciliation</h5>
                        <p className="text-muted">Reconcile bank statements with transactions</p>
                        <Button variant="success" href="/bank-reconciliation">
                          Start Reconciliation
                        </Button>
                      </Card.Body>
                    </Card>
                  </Col>

                  <Col lg={4} md={6} className="mb-3">
                    <Card className="dashboard-card h-100">
                      <Card.Body className="text-center">
                        <i className="fas fa-file-upload fa-3x text-info mb-3"></i>
                        <h5>File Interaction</h5>
                        <p className="text-muted">Upload and manage your accounting files</p>
                        <Button variant="info" href="/file-interaction">
                          Manage Files
                        </Button>
                      </Card.Body>
                    </Card>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Portal Access */}
        <Row>
          <Col>
            <Card>
              <Card.Header>
                <h5 className="mb-0">Portal Access</h5>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col lg={2} md={4} sm={6} className="mb-3">
                    <Button variant="outline-primary" className="w-100" href="/portals/invoice">
                      <i className="fas fa-receipt d-block mb-2"></i>
                      Invoice Portal
                    </Button>
                  </Col>
                  <Col lg={2} md={4} sm={6} className="mb-3">
                    <Button variant="outline-secondary" className="w-100" href="/portals/inventory">
                      <i className="fas fa-boxes d-block mb-2"></i>
                      Inventory Portal
                    </Button>
                  </Col>
                  <Col lg={2} md={4} sm={6} className="mb-3">
                    <Button variant="outline-success" className="w-100" href="/portals/gst">
                      <i className="fas fa-percentage d-block mb-2"></i>
                      GST Portal
                    </Button>
                  </Col>
                  <Col lg={2} md={4} sm={6} className="mb-3">
                    <Button variant="outline-warning" className="w-100" href="/portals/audit">
                      <i className="fas fa-search d-block mb-2"></i>
                      Audit Portal
                    </Button>
                  </Col>
                  <Col lg={2} md={4} sm={6} className="mb-3">
                    <Button variant="outline-info" className="w-100" href="/portals/reports">
                      <i className="fas fa-chart-bar d-block mb-2"></i>
                      Reports Portal
                    </Button>
                  </Col>
                  <Col lg={2} md={4} sm={6} className="mb-3">
                    <Button variant="outline-dark" className="w-100" href="/portals/ai-insights">
                      <i className="fas fa-brain d-block mb-2"></i>
                      AI Insights
                    </Button>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </>
  )
}
