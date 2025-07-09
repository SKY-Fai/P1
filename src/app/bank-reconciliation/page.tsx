
'use client'

import { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Button, Form, Alert, Table, Badge, Modal } from 'react-bootstrap'
import Navigation from '@/components/Navigation'

interface BankTransaction {
  id: string
  date: string
  description: string
  amount: number
  type: string
  status: string
  confidence?: number
  match_details?: string
}

export default function BankReconciliation() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [processing, setProcessing] = useState(false)
  const [transactions, setTransactions] = useState<BankTransaction[]>([])
  const [showMappingModal, setShowMappingModal] = useState(false)
  const [selectedTransaction, setSelectedTransaction] = useState<BankTransaction | null>(null)
  const [selectedAccount, setSelectedAccount] = useState('')
  const [mappingNotes, setMappingNotes] = useState('')
  const [error, setError] = useState('')

  const chartOfAccounts = [
    { code: '1000', name: 'Cash and Cash Equivalents' },
    { code: '1020', name: 'Bank Account - Current' },
    { code: '1100', name: 'Accounts Receivable' },
    { code: '2010', name: 'Accounts Payable' },
    { code: '4000', name: 'Sales Revenue' },
    { code: '4100', name: 'Interest Income' },
    { code: '5110', name: 'Salaries and Wages' },
    { code: '5120', name: 'Rent Expense' },
    { code: '5200', name: 'Bank Charges' }
  ]

  const handleFileUpload = async () => {
    if (!selectedFile) {
      setError('Please select a bank statement file')
      return
    }

    setProcessing(true)
    setError('')

    const formData = new FormData()
    formData.append('bankStatementFile', selectedFile)
    formData.append('bank_name', 'Sample Bank')
    formData.append('account_type', 'current')

    try {
      const response = await fetch('/api/bank-reconciliation/process', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setTransactions(data.results || [])
      } else {
        setError('Failed to process bank statement')
      }
    } catch (err) {
      setError('Network error occurred')
    } finally {
      setProcessing(false)
    }
  }

  const openMappingModal = (transaction: BankTransaction) => {
    setSelectedTransaction(transaction)
    setSelectedAccount('')
    setMappingNotes('')
    setShowMappingModal(true)
  }

  const handleManualMapping = async () => {
    if (!selectedTransaction || !selectedAccount) return

    try {
      const response = await fetch('/api/bank-reconciliation/manual-map', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transaction_id: selectedTransaction.id,
          account_code: selectedAccount,
          notes: mappingNotes,
          mapping_type: 'manual'
        })
      })

      if (response.ok) {
        // Update transaction status
        setTransactions(prev => 
          prev.map(t => 
            t.id === selectedTransaction.id 
              ? { ...t, status: 'mapped' }
              : t
          )
        )
        setShowMappingModal(false)
      }
    } catch (error) {
      console.error('Mapping failed:', error)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'matched':
        return <Badge bg="success">Matched</Badge>
      case 'unmatched':
        return <Badge bg="danger">Unmatched</Badge>
      case 'partial':
        return <Badge bg="warning">Partial</Badge>
      case 'mapped':
        return <Badge bg="info">Mapped</Badge>
      default:
        return <Badge bg="secondary">{status}</Badge>
    }
  }

  return (
    <>
      <Navigation />
      <Container fluid className="pt-5 mt-3">
        <Row>
          <Col>
            <h1 className="mb-4">Bank Reconciliation</h1>
          </Col>
        </Row>

        {/* Upload Section */}
        <Row className="mb-4">
          <Col>
            <Card>
              <Card.Header>
                <h5 className="mb-0">Upload Bank Statement</h5>
              </Card.Header>
              <Card.Body>
                {error && (
                  <Alert variant="danger" className="mb-3">
                    {error}
                  </Alert>
                )}

                <Form>
                  <Row>
                    <Col md={8}>
                      <Form.Group className="mb-3">
                        <Form.Label>Bank Statement File</Form.Label>
                        <Form.Control 
                          type="file" 
                          accept=".xlsx,.xls,.csv"
                          onChange={(e) => {
                            const files = (e.target as HTMLInputElement).files
                            if (files && files[0]) {
                              setSelectedFile(files[0])
                            }
                          }}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={4} className="d-flex align-items-end">
                      <Button 
                        variant="primary" 
                        onClick={handleFileUpload}
                        disabled={processing || !selectedFile}
                        className="mb-3"
                      >
                        {processing ? 'Processing...' : 'Process Statement'}
                      </Button>
                    </Col>
                  </Row>
                </Form>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Transactions Table */}
        {transactions.length > 0 && (
          <Row>
            <Col>
              <Card>
                <Card.Header>
                  <h5 className="mb-0">Bank Transactions</h5>
                </Card.Header>
                <Card.Body>
                  <Table responsive striped>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Amount</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Confidence</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((transaction) => (
                        <tr key={transaction.id}>
                          <td>{transaction.date}</td>
                          <td>{transaction.description}</td>
                          <td className={transaction.amount > 0 ? 'text-success' : 'text-danger'}>
                            ${Math.abs(transaction.amount).toLocaleString()}
                          </td>
                          <td>{transaction.type}</td>
                          <td>{getStatusBadge(transaction.status)}</td>
                          <td>
                            {transaction.confidence 
                              ? `${transaction.confidence}%` 
                              : '-'
                            }
                          </td>
                          <td>
                            {transaction.status === 'unmatched' && (
                              <Button 
                                variant="outline-primary" 
                                size="sm"
                                onClick={() => openMappingModal(transaction)}
                              >
                                Map Manually
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}

        {/* Manual Mapping Modal */}
        <Modal show={showMappingModal} onHide={() => setShowMappingModal(false)}>
          <Modal.Header closeButton>
            <Modal.Title>Manual Transaction Mapping</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {selectedTransaction && (
              <>
                <div className="mb-3">
                  <strong>Transaction:</strong> {selectedTransaction.description}<br />
                  <strong>Amount:</strong> ${Math.abs(selectedTransaction.amount).toLocaleString()}<br />
                  <strong>Date:</strong> {selectedTransaction.date}
                </div>

                <Form.Group className="mb-3">
                  <Form.Label>Select Account</Form.Label>
                  <Form.Select 
                    value={selectedAccount} 
                    onChange={(e) => setSelectedAccount(e.target.value)}
                  >
                    <option value="">Choose account...</option>
                    {chartOfAccounts.map((account) => (
                      <option key={account.code} value={account.code}>
                        {account.code} - {account.name}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Notes (Optional)</Form.Label>
                  <Form.Control 
                    as="textarea" 
                    rows={3}
                    value={mappingNotes}
                    onChange={(e) => setMappingNotes(e.target.value)}
                    placeholder="Enter any additional notes for this mapping..."
                  />
                </Form.Group>
              </>
            )}
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowMappingModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleManualMapping}
              disabled={!selectedAccount}
            >
              Create Mapping
            </Button>
          </Modal.Footer>
        </Modal>
      </Container>
    </>
  )
}
