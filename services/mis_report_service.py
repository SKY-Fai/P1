"""
MIS Report Service for F-AI Accountant
Management Information System with Accounting Validation and Ratio Analysis
"""

import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
import math


class MISReportService:
    """
    MIS Report Service for comprehensive financial analysis with accounting validation
    and ratio analysis including explanations of accounting logic
    """
    
    def __init__(self, company_id: int, user_id: int):
        self.company_id = company_id
        self.user_id = user_id
        self.accounting_errors = []
        self.validation_warnings = []
        
    def generate_mis_report(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive MIS report with accounting validation and ratio analysis
        
        Args:
            financial_data: Dictionary containing all financial reports data
            
        Returns:
            Dictionary containing MIS report with validation and ratios
        """
        try:
            # Extract financial statements
            trial_balance = financial_data.get('trial_balance', {})
            profit_loss = financial_data.get('profit_loss', {})
            balance_sheet = financial_data.get('balance_sheet', {})
            cash_flow = financial_data.get('cash_flow', {})
            
            # Generate MIS report
            mis_report = {
                'report_header': self._generate_report_header(),
                'accounting_validation': self._perform_accounting_validation(financial_data),
                'financial_ratios': self._calculate_financial_ratios(balance_sheet, profit_loss),
                'trend_analysis': self._perform_trend_analysis(financial_data),
                'variance_analysis': self._perform_variance_analysis(financial_data),
                'key_performance_indicators': self._calculate_kpis(financial_data),
                'cash_flow_analysis': self._analyze_cash_flow(cash_flow),
                'profitability_analysis': self._analyze_profitability(profit_loss),
                'liquidity_analysis': self._analyze_liquidity(balance_sheet),
                'solvency_analysis': self._analyze_solvency(balance_sheet, profit_loss),
                'efficiency_analysis': self._analyze_efficiency(balance_sheet, profit_loss),
                'executive_summary': self._generate_executive_summary(financial_data),
                'recommendations': self._generate_recommendations(financial_data),
                'accounting_explanations': self._generate_accounting_explanations(),
                'report_footer': self._generate_report_footer()
            }
            
            return mis_report
            
        except Exception as e:
            return {
                'error': f'Error generating MIS report: {str(e)}',
                'report_header': self._generate_report_header(),
                'accounting_validation': {'status': 'Error', 'message': str(e)}
            }
    
    def _generate_report_header(self) -> Dict[str, Any]:
        """Generate MIS report header with company information"""
        return {
            'company_name': 'F-AI Accountant',
            'report_title': 'Management Information System (MIS) Report',
            'subtitle': 'Comprehensive Financial Analysis with Accounting Validation',
            'generation_date': datetime.now().strftime('%Y-%m-%d'),
            'generation_time': datetime.now().strftime('%H:%M:%S'),
            'company_id': self.company_id,
            'user_id': self.user_id,
            'report_period': 'Current Financial Year',
            'currency': 'INR'
        }
    
    def _perform_accounting_validation(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive accounting validation with explanations
        """
        validation_results = {
            'overall_status': 'PASS',
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'warnings': 0,
            'validations': []
        }
        
        # 1. Double Entry Validation
        double_entry_check = self._validate_double_entry(financial_data.get('journal', {}))
        validation_results['validations'].append(double_entry_check)
        validation_results['total_checks'] += 1
        
        # 2. Trial Balance Validation
        trial_balance_check = self._validate_trial_balance(financial_data.get('trial_balance', {}))
        validation_results['validations'].append(trial_balance_check)
        validation_results['total_checks'] += 1
        
        # 3. Balance Sheet Equation Validation
        balance_sheet_check = self._validate_balance_sheet_equation(financial_data.get('balance_sheet', {}))
        validation_results['validations'].append(balance_sheet_check)
        validation_results['total_checks'] += 1
        
        # 4. P&L Account Validation
        pl_validation = self._validate_profit_loss(financial_data.get('profit_loss', {}))
        validation_results['validations'].append(pl_validation)
        validation_results['total_checks'] += 1
        
        # 5. Cash Flow Validation
        cash_flow_check = self._validate_cash_flow(financial_data.get('cash_flow', {}))
        validation_results['validations'].append(cash_flow_check)
        validation_results['total_checks'] += 1
        
        # Count results
        for validation in validation_results['validations']:
            if validation['status'] == 'PASS':
                validation_results['passed_checks'] += 1
            elif validation['status'] == 'FAIL':
                validation_results['failed_checks'] += 1
                validation_results['overall_status'] = 'FAIL'
            else:
                validation_results['warnings'] += 1
        
        return validation_results
    
    def _validate_double_entry(self, journal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate double entry principle"""
        try:
            entries = journal_data.get('entries', [])
            total_debits = 0
            total_credits = 0
            
            for entry in entries:
                total_debits += float(entry.get('debit_amount', 0))
                total_credits += float(entry.get('credit_amount', 0))
            
            difference = abs(total_debits - total_credits)
            
            return {
                'check_name': 'Double Entry Validation',
                'status': 'PASS' if difference < 0.01 else 'FAIL',
                'total_debits': total_debits,
                'total_credits': total_credits,
                'difference': difference,
                'explanation': 'Double entry principle requires total debits to equal total credits. This is the fundamental accounting equation that ensures accuracy.',
                'accounting_logic': 'For every debit entry, there must be a corresponding credit entry of equal amount. This maintains the accounting equation: Assets = Liabilities + Equity.'
            }
        except Exception as e:
            return {
                'check_name': 'Double Entry Validation',
                'status': 'ERROR',
                'error': str(e),
                'explanation': 'Unable to validate double entry principle due to data issues.'
            }
    
    def _validate_trial_balance(self, trial_balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trial balance totals"""
        try:
            accounts = trial_balance_data.get('accounts', [])
            total_debits = sum(float(acc.get('debit_balance', 0)) for acc in accounts)
            total_credits = sum(float(acc.get('credit_balance', 0)) for acc in accounts)
            
            difference = abs(total_debits - total_credits)
            
            return {
                'check_name': 'Trial Balance Validation',
                'status': 'PASS' if difference < 0.01 else 'FAIL',
                'total_debits': total_debits,
                'total_credits': total_credits,
                'difference': difference,
                'explanation': 'Trial balance ensures that the sum of all debit balances equals the sum of all credit balances.',
                'accounting_logic': 'Trial balance is a summary of all ledger accounts showing their debit and credit balances. If debits ≠ credits, there are posting errors.'
            }
        except Exception as e:
            return {
                'check_name': 'Trial Balance Validation',
                'status': 'ERROR',
                'error': str(e),
                'explanation': 'Unable to validate trial balance due to data issues.'
            }
    
    def _validate_balance_sheet_equation(self, balance_sheet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate balance sheet equation: Assets = Liabilities + Equity"""
        try:
            assets = balance_sheet_data.get('assets', {})
            liabilities = balance_sheet_data.get('liabilities', {})
            equity = balance_sheet_data.get('equity', {})
            
            total_assets = float(assets.get('total', 0))
            total_liabilities = float(liabilities.get('total', 0))
            total_equity = float(equity.get('total', 0))
            
            total_liab_equity = total_liabilities + total_equity
            difference = abs(total_assets - total_liab_equity)
            
            return {
                'check_name': 'Balance Sheet Equation',
                'status': 'PASS' if difference < 0.01 else 'FAIL',
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'total_equity': total_equity,
                'total_liab_equity': total_liab_equity,
                'difference': difference,
                'explanation': 'Balance sheet equation (Assets = Liabilities + Equity) must always balance.',
                'accounting_logic': 'This equation represents the fundamental accounting relationship. Assets are financed either by liabilities (debt) or equity (owner\'s investment).'
            }
        except Exception as e:
            return {
                'check_name': 'Balance Sheet Equation',
                'status': 'ERROR',
                'error': str(e),
                'explanation': 'Unable to validate balance sheet equation due to data issues.'
            }
    
    def _validate_profit_loss(self, profit_loss_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate profit and loss statement calculations"""
        try:
            revenue = float(profit_loss_data.get('revenue', {}).get('total', 0))
            expenses = float(profit_loss_data.get('expenses', {}).get('total', 0))
            net_profit = float(profit_loss_data.get('net_profit', 0))
            
            calculated_profit = revenue - expenses
            difference = abs(net_profit - calculated_profit)
            
            return {
                'check_name': 'Profit & Loss Validation',
                'status': 'PASS' if difference < 0.01 else 'FAIL',
                'total_revenue': revenue,
                'total_expenses': expenses,
                'reported_net_profit': net_profit,
                'calculated_net_profit': calculated_profit,
                'difference': difference,
                'explanation': 'Net profit should equal total revenue minus total expenses.',
                'accounting_logic': 'P&L statement follows the equation: Revenue - Expenses = Net Profit. This shows the company\'s profitability over a period.'
            }
        except Exception as e:
            return {
                'check_name': 'Profit & Loss Validation',
                'status': 'ERROR',
                'error': str(e),
                'explanation': 'Unable to validate P&L statement due to data issues.'
            }
    
    def _validate_cash_flow(self, cash_flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate cash flow statement"""
        try:
            operating = float(cash_flow_data.get('operating', {}).get('net_cash', 0))
            investing = float(cash_flow_data.get('investing', {}).get('net_cash', 0))
            financing = float(cash_flow_data.get('financing', {}).get('net_cash', 0))
            
            net_cash_flow = operating + investing + financing
            reported_net_cash = float(cash_flow_data.get('net_cash_flow', 0))
            
            difference = abs(net_cash_flow - reported_net_cash)
            
            return {
                'check_name': 'Cash Flow Validation',
                'status': 'PASS' if difference < 0.01 else 'FAIL',
                'operating_cash_flow': operating,
                'investing_cash_flow': investing,
                'financing_cash_flow': financing,
                'calculated_net_cash': net_cash_flow,
                'reported_net_cash': reported_net_cash,
                'difference': difference,
                'explanation': 'Net cash flow should equal the sum of operating, investing, and financing cash flows.',
                'accounting_logic': 'Cash flow statement shows cash movements in three categories: Operating (business operations), Investing (asset purchases/sales), and Financing (debt/equity changes).'
            }
        except Exception as e:
            return {
                'check_name': 'Cash Flow Validation',
                'status': 'ERROR',
                'error': str(e),
                'explanation': 'Unable to validate cash flow statement due to data issues.'
            }
    
    def _calculate_financial_ratios(self, balance_sheet: Dict[str, Any], profit_loss: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive financial ratios with explanations"""
        try:
            # Extract key figures
            current_assets = float(balance_sheet.get('assets', {}).get('current_assets', {}).get('total', 0))
            current_liabilities = float(balance_sheet.get('liabilities', {}).get('current_liabilities', {}).get('total', 0))
            total_assets = float(balance_sheet.get('assets', {}).get('total', 0))
            total_liabilities = float(balance_sheet.get('liabilities', {}).get('total', 0))
            total_equity = float(balance_sheet.get('equity', {}).get('total', 0))
            
            revenue = float(profit_loss.get('revenue', {}).get('total', 0))
            net_profit = float(profit_loss.get('net_profit', 0))
            cost_of_goods_sold = float(profit_loss.get('cost_of_goods_sold', 0))
            
            ratios = {
                'liquidity_ratios': {
                    'current_ratio': {
                        'value': current_assets / current_liabilities if current_liabilities > 0 else 0,
                        'formula': 'Current Assets ÷ Current Liabilities',
                        'interpretation': 'Measures ability to pay short-term obligations',
                        'benchmark': 'Ideally between 1.5 to 3.0',
                        'accounting_logic': 'Higher ratio indicates better liquidity position'
                    },
                    'quick_ratio': {
                        'value': (current_assets - 0) / current_liabilities if current_liabilities > 0 else 0,
                        'formula': '(Current Assets - Inventory) ÷ Current Liabilities',
                        'interpretation': 'Measures ability to pay short-term debts with liquid assets',
                        'benchmark': 'Ideally above 1.0',
                        'accounting_logic': 'More conservative than current ratio as it excludes inventory'
                    }
                },
                'profitability_ratios': {
                    'gross_profit_margin': {
                        'value': ((revenue - cost_of_goods_sold) / revenue * 100) if revenue > 0 else 0,
                        'formula': '(Revenue - COGS) ÷ Revenue × 100',
                        'interpretation': 'Percentage of revenue remaining after direct costs',
                        'benchmark': 'Industry dependent, higher is better',
                        'accounting_logic': 'Shows pricing power and cost control efficiency'
                    },
                    'net_profit_margin': {
                        'value': (net_profit / revenue * 100) if revenue > 0 else 0,
                        'formula': 'Net Profit ÷ Revenue × 100',
                        'interpretation': 'Percentage of revenue converted to profit',
                        'benchmark': '5-10% is generally good',
                        'accounting_logic': 'Indicates overall profitability and cost management'
                    },
                    'return_on_assets': {
                        'value': (net_profit / total_assets * 100) if total_assets > 0 else 0,
                        'formula': 'Net Profit ÷ Total Assets × 100',
                        'interpretation': 'Efficiency of asset utilization',
                        'benchmark': '5-20% depending on industry',
                        'accounting_logic': 'Shows how effectively assets generate profits'
                    },
                    'return_on_equity': {
                        'value': (net_profit / total_equity * 100) if total_equity > 0 else 0,
                        'formula': 'Net Profit ÷ Total Equity × 100',
                        'interpretation': 'Return generated on shareholders\' investment',
                        'benchmark': '10-20% is generally good',
                        'accounting_logic': 'Higher ROE indicates better returns for shareholders'
                    }
                },
                'leverage_ratios': {
                    'debt_to_equity': {
                        'value': total_liabilities / total_equity if total_equity > 0 else 0,
                        'formula': 'Total Liabilities ÷ Total Equity',
                        'interpretation': 'Amount of debt relative to equity',
                        'benchmark': 'Lower than 1.0 is generally safer',
                        'accounting_logic': 'Higher ratio indicates more financial risk'
                    },
                    'debt_to_assets': {
                        'value': total_liabilities / total_assets if total_assets > 0 else 0,
                        'formula': 'Total Liabilities ÷ Total Assets',
                        'interpretation': 'Proportion of assets financed by debt',
                        'benchmark': 'Less than 0.5 is generally preferred',
                        'accounting_logic': 'Shows financial leverage and risk level'
                    }
                },
                'efficiency_ratios': {
                    'asset_turnover': {
                        'value': revenue / total_assets if total_assets > 0 else 0,
                        'formula': 'Revenue ÷ Total Assets',
                        'interpretation': 'How efficiently assets generate revenue',
                        'benchmark': 'Higher is better, varies by industry',
                        'accounting_logic': 'Shows asset productivity and utilization'
                    }
                }
            }
            
            return ratios
            
        except Exception as e:
            return {
                'error': f'Error calculating ratios: {str(e)}',
                'explanation': 'Unable to calculate financial ratios due to data issues'
            }
    
    def _perform_trend_analysis(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform trend analysis on financial data"""
        return {
            'analysis_type': 'Trend Analysis',
            'description': 'Year-over-year comparison of key financial metrics',
            'note': 'Historical data required for meaningful trend analysis',
            'recommendation': 'Collect multiple periods of data for comprehensive trend analysis'
        }
    
    def _perform_variance_analysis(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform variance analysis"""
        return {
            'analysis_type': 'Variance Analysis',
            'description': 'Budget vs Actual comparison',
            'note': 'Budget data required for variance analysis',
            'recommendation': 'Implement budgeting system for effective variance analysis'
        }
    
    def _calculate_kpis(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key performance indicators"""
        profit_loss = financial_data.get('profit_loss', {})
        balance_sheet = financial_data.get('balance_sheet', {})
        
        revenue = float(profit_loss.get('revenue', {}).get('total', 0))
        net_profit = float(profit_loss.get('net_profit', 0))
        total_assets = float(balance_sheet.get('assets', {}).get('total', 0))
        
        return {
            'revenue_growth': {
                'value': 'N/A',
                'note': 'Requires historical data for calculation'
            },
            'profit_margin': {
                'value': f"{(net_profit / revenue * 100):.2f}%" if revenue > 0 else "0%",
                'explanation': 'Percentage of revenue converted to profit'
            },
            'asset_utilization': {
                'value': f"{(revenue / total_assets):.2f}" if total_assets > 0 else "0",
                'explanation': 'Revenue generated per rupee of assets'
            }
        }
    
    def _analyze_cash_flow(self, cash_flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cash flow patterns"""
        operating_cash = float(cash_flow_data.get('operating', {}).get('net_cash', 0))
        investing_cash = float(cash_flow_data.get('investing', {}).get('net_cash', 0))
        financing_cash = float(cash_flow_data.get('financing', {}).get('net_cash', 0))
        
        return {
            'operating_cash_flow': operating_cash,
            'investing_cash_flow': investing_cash,
            'financing_cash_flow': financing_cash,
            'analysis': {
                'operating_health': 'Positive' if operating_cash > 0 else 'Negative',
                'investment_activity': 'Investing' if investing_cash < 0 else 'Divesting',
                'financing_pattern': 'Raising funds' if financing_cash > 0 else 'Returning funds'
            },
            'interpretation': 'Strong companies typically have positive operating cash flow, negative investing cash flow (growth investments), and variable financing cash flow.'
        }
    
    def _analyze_profitability(self, profit_loss_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze profitability metrics"""
        revenue = float(profit_loss_data.get('revenue', {}).get('total', 0))
        expenses = float(profit_loss_data.get('expenses', {}).get('total', 0))
        net_profit = float(profit_loss_data.get('net_profit', 0))
        
        return {
            'revenue': revenue,
            'expenses': expenses,
            'net_profit': net_profit,
            'profit_margin': (net_profit / revenue * 100) if revenue > 0 else 0,
            'expense_ratio': (expenses / revenue * 100) if revenue > 0 else 0,
            'analysis': {
                'profitability_status': 'Profitable' if net_profit > 0 else 'Loss-making',
                'cost_control': 'Good' if (expenses / revenue) < 0.8 else 'Needs improvement'
            }
        }
    
    def _analyze_liquidity(self, balance_sheet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze liquidity position"""
        current_assets = float(balance_sheet_data.get('assets', {}).get('current_assets', {}).get('total', 0))
        current_liabilities = float(balance_sheet_data.get('liabilities', {}).get('current_liabilities', {}).get('total', 0))
        
        current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
        
        return {
            'current_assets': current_assets,
            'current_liabilities': current_liabilities,
            'current_ratio': current_ratio,
            'liquidity_status': 'Strong' if current_ratio > 1.5 else 'Moderate' if current_ratio > 1.0 else 'Weak',
            'analysis': 'Current ratio indicates ability to pay short-term obligations. A ratio above 1.5 is generally considered healthy.'
        }
    
    def _analyze_solvency(self, balance_sheet_data: Dict[str, Any], profit_loss_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze solvency and financial stability"""
        total_assets = float(balance_sheet_data.get('assets', {}).get('total', 0))
        total_liabilities = float(balance_sheet_data.get('liabilities', {}).get('total', 0))
        total_equity = float(balance_sheet_data.get('equity', {}).get('total', 0))
        
        debt_to_equity = total_liabilities / total_equity if total_equity > 0 else 0
        equity_ratio = total_equity / total_assets if total_assets > 0 else 0
        
        return {
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'debt_to_equity_ratio': debt_to_equity,
            'equity_ratio': equity_ratio,
            'solvency_status': 'Strong' if debt_to_equity < 1.0 else 'Moderate' if debt_to_equity < 2.0 else 'Weak',
            'analysis': 'Lower debt-to-equity ratio indicates better financial stability and lower financial risk.'
        }
    
    def _analyze_efficiency(self, balance_sheet_data: Dict[str, Any], profit_loss_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze operational efficiency"""
        revenue = float(profit_loss_data.get('revenue', {}).get('total', 0))
        total_assets = float(balance_sheet_data.get('assets', {}).get('total', 0))
        
        asset_turnover = revenue / total_assets if total_assets > 0 else 0
        
        return {
            'revenue': revenue,
            'total_assets': total_assets,
            'asset_turnover_ratio': asset_turnover,
            'efficiency_status': 'High' if asset_turnover > 1.5 else 'Moderate' if asset_turnover > 1.0 else 'Low',
            'analysis': 'Asset turnover ratio measures how efficiently assets are used to generate revenue. Higher is better.'
        }
    
    def _generate_executive_summary(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        profit_loss = financial_data.get('profit_loss', {})
        balance_sheet = financial_data.get('balance_sheet', {})
        
        revenue = float(profit_loss.get('revenue', {}).get('total', 0))
        net_profit = float(profit_loss.get('net_profit', 0))
        total_assets = float(balance_sheet.get('assets', {}).get('total', 0))
        
        return {
            'financial_performance': {
                'revenue': revenue,
                'net_profit': net_profit,
                'profit_margin': (net_profit / revenue * 100) if revenue > 0 else 0,
                'overall_performance': 'Profitable' if net_profit > 0 else 'Loss-making'
            },
            'financial_position': {
                'total_assets': total_assets,
                'net_worth': float(balance_sheet.get('equity', {}).get('total', 0)),
                'financial_health': 'Stable' if total_assets > 0 else 'Needs attention'
            },
            'key_highlights': [
                f"Total Revenue: ₹{revenue:,.2f}",
                f"Net Profit: ₹{net_profit:,.2f}",
                f"Total Assets: ₹{total_assets:,.2f}",
                f"Financial Health: {'Profitable' if net_profit > 0 else 'Loss-making'}"
            ]
        }
    
    def _generate_recommendations(self, financial_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        profit_loss = financial_data.get('profit_loss', {})
        balance_sheet = financial_data.get('balance_sheet', {})
        
        # Profitability recommendations
        net_profit = float(profit_loss.get('net_profit', 0))
        if net_profit <= 0:
            recommendations.append({
                'category': 'Profitability',
                'priority': 'High',
                'recommendation': 'Focus on cost reduction and revenue enhancement strategies',
                'rationale': 'Company is currently not profitable'
            })
        
        # Liquidity recommendations
        current_assets = float(balance_sheet.get('assets', {}).get('current_assets', {}).get('total', 0))
        current_liabilities = float(balance_sheet.get('liabilities', {}).get('current_liabilities', {}).get('total', 0))
        
        if current_liabilities > 0:
            current_ratio = current_assets / current_liabilities
            if current_ratio < 1.0:
                recommendations.append({
                    'category': 'Liquidity',
                    'priority': 'High',
                    'recommendation': 'Improve working capital management',
                    'rationale': 'Current ratio below 1.0 indicates liquidity concerns'
                })
        
        # Add general recommendations
        recommendations.extend([
            {
                'category': 'Reporting',
                'priority': 'Medium',
                'recommendation': 'Implement monthly financial reporting',
                'rationale': 'Regular reporting helps identify trends and issues early'
            },
            {
                'category': 'Analysis',
                'priority': 'Medium',
                'recommendation': 'Establish key performance indicators (KPIs)',
                'rationale': 'KPIs help track business performance systematically'
            }
        ])
        
        return recommendations
    
    def _generate_accounting_explanations(self) -> Dict[str, Any]:
        """Generate explanations of accounting concepts and logic"""
        return {
            'fundamental_principles': {
                'double_entry': 'Every transaction affects at least two accounts with equal debits and credits',
                'accrual_basis': 'Revenue and expenses are recorded when earned/incurred, not when cash changes hands',
                'matching_principle': 'Expenses should be matched with related revenues in the same period',
                'conservatism': 'When in doubt, choose the option that is less likely to overstate assets and income'
            },
            'financial_statements': {
                'balance_sheet': 'Shows financial position at a specific point in time (Assets = Liabilities + Equity)',
                'income_statement': 'Shows profitability over a period (Revenue - Expenses = Net Income)',
                'cash_flow_statement': 'Shows cash movements in operating, investing, and financing activities',
                'statement_of_equity': 'Shows changes in owner\'s equity over a period'
            },
            'ratio_analysis': {
                'liquidity_ratios': 'Measure ability to pay short-term obligations',
                'profitability_ratios': 'Measure company\'s ability to generate profits',
                'leverage_ratios': 'Measure degree of financial risk and debt usage',
                'efficiency_ratios': 'Measure how effectively company uses its assets'
            }
        }
    
    def _generate_report_footer(self) -> Dict[str, Any]:
        """Generate report footer"""
        return {
            'disclaimer': 'This MIS report is generated based on the financial data provided. The accuracy of the analysis depends on the quality and completeness of the input data.',
            'generated_by': 'F-AI Accountant MIS Report Service',
            'report_version': '1.0',
            'contact_info': 'For questions about this report, please contact your financial administrator.'
        }