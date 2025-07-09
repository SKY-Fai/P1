
'use client'

import { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Button, Form, Alert, Table, ProgressBar } from 'react-bootstrap'
import Navigation from '@/components/Navigation'

export default function AIAccounting() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [templateType, setTemplateType] = useState('')
  const [processing, setProcessing] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [error, setError] = useState('')

  const templateTypes = [
    { value: 'purchase', label: 'Purchase Transactions' },
    { value: 'sales', label: 'Sales Transactions' },
    { value: 'income', label: 'Income Transactions' },
    { value: 'expense', label: 'Expense Transactions' },
    { value: 'credit_note', label: 'Credit Note' },
    { value: 'debit_note', label: 'Debit Note' },
    { value: 'combined_all', label: 'Combined All Templates' }
  ]

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
      setError('')
    }
  }

  const handleProcessFile = async () => {
    if (!selectedFile || !templateType) {
      setError('Please select a file and template type')
      return
    }

    setProcessing(true)
    setError('')
    setResults(null)

    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('template_type', templateType)

    try {
      const response = await fetch('/api/automated-accounting/process', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data)
      } else {
        const errorData = await response.json()
        setError(errorData.error || 'Processing failed')
      }
    } catch (err) {
      setError('Network error occurred')
    } finally {
      setProcessing(false)
    }
  }

  const downloadTemplate = async (type: string) => {
    try {
      const response = await fetch(`/download-accounting-template/${type}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${type}_template.xlsx`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  return (
    <>
      <Navigation />
      <Container fluid className="pt-5 mt-3">
        <Row>
          <Col>
            <h1 className="mb-4">AI Accounting Dashboard</h1>
          </Col>
        </Row>

        {/* Template Downloads */}
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h5 className="mb-0">Download Templates</h5>
              </Card.Header>
              <Card.Body>
                <Row>
                  {templateTypes.slice(0, -1).map((template) => (
                    <Col lg={4} md={6} className="mb-3" key={template.value}>
                      <Card className="dashboard-card h-100">
                        <Card.Body className="text-center">
                          <h6>{template.label}</h6>
                          <Button 
                            variant="outline-primary" 
                            size="sm"
                            onClick={() => downloadTemplate(template.value)}
                          >
                            Download Template
                          </Button>
                        </Card.Body>
                      </Card>
                    </Col>
                  ))}
                </Row>
                <hr />
                <div className="text-center">
                  <Button 
                    variant="success" 
                    onClick={() => downloadTemplate('combined_all')}
                  >
                    Download Combined Template (All Types)
                  </Button>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* File Upload and Processing */}
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h5 className="mb-0">Upload & Process Files</h5>
              </Card.Header>
              <Card.Body>
                {error && (
                  <Alert variant="danger" className="mb-3">
                    {error}
                  </Alert>
                )}

                <Form>
                  <Row>
                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Select Template Type</Form.Label>
                        <Form.Select 
                          value={templateType} 
                          onChange={(e) => setTemplateType(e.target.value)}
                        >
                          <option value="">Choose template type...</option>
                          {templateTypes.map((template) => (
                            <option key={template.value} value={template.value}>
                              {template.label}
                            </option>
                          ))}
                        </Form.Select>
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Upload File</Form.Label>
                        <Form.Control 
                          type="file" 
                          accept=".xlsx,.xls,.csv"
                          onChange={handleFileChange}
                        />
                      </Form.Group>
                    </Col>
                  </Row>

                  <Button 
                    variant="primary" 
                    onClick={handleProcessFile}
                    disabled={processing || !selectedFile || !templateType}
                  >
                    {processing ? 'Processing...' : 'Process File'}
                  </Button>
                </Form>

                {processing && (
                  <div className="mt-3">
                    <ProgressBar animated now={100} />
                    <small className="text-muted">Processing your file...</small>
                  </div>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Results */}
        {results && (
          <Row>
            <Col>
              <Card>
                <Card.Header>
                  <h5 className="mb-0">Processing Results</h5>
                </Card.Header>
                <Card.Body>
                  <Alert variant="success">
                    File processed successfully! Generated {results.total_entries} journal entries.
                  </Alert>
                  
                  <Row className="mb-3">
                    <Col md={4}>
                      <Card className="text-center">
                        <Card.Body>
                          <h3 className="text-primary">{results.total_entries}</h3>
                          <p className="mb-0">Total Entries</p>
                        </Card.Body>
                      </Card>
                    </Col>
                    <Col md={4}>
                      <Card className="text-center">
                        <Card.Body>
                          <h3 className="text-success">
                            {results.balance_verification ? 'Balanced' : 'Unbalanced'}
                          </h3>
                          <p className="mb-0">Balance Check</p>
                        </Card.Body>
                      </Card>
                    </Col>
                    <Col md={4}>
                      <Card className="text-center">
                        <Card.Body>
                          <h3 className="text-info">{results.generated_reports?.length || 0}</h3>
                          <p className="mb-0">Reports Generated</p>
                        </Card.Body>
                      </Card>
                    </Col>
                  </Row>

                  <div className="d-flex gap-2">
                    <Button variant="outline-primary">Download Journal Report</Button>
                    <Button variant="outline-success">Download Trial Balance</Button>
                    <Button variant="outline-info">Download All Reports</Button>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}
      </Container>
    </>
  )
}
