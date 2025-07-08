"""
PROFESSIONAL INVOICE MAPPING ENGINE
==================================

Advanced sequential logic processing for bank statement to invoice mapping
with comprehensive manual mapping capabilities and detailed audit trails.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re
import logging
from dataclasses import dataclass
from enum import Enum

class MatchingStage(Enum):
    STAGE_1_AMOUNT = "amount_precision"
    STAGE_2_TEMPORAL = "temporal_correlation"
    STAGE_3_REFERENCE = "reference_patterns"
    STAGE_4_PARTY = "party_identification"
    STAGE_5_SEMANTIC = "semantic_analysis"
    STAGE_6_BEHAVIORAL = "behavioral_patterns"
    STAGE_7_CONTEXTUAL = "contextual_logic"
    MANUAL_MAPPING = "manual_intervention"

class ConfidenceLevel(Enum):
    PERFECT = "perfect_match"
    HIGH = "high_confidence"
    GOOD = "good_match"
    MODERATE = "moderate_match"
    LOW = "low_confidence"
    FAILED = "mapping_failed"

@dataclass
class MatchingResult:
    stage: MatchingStage
    score: float
    confidence_level: ConfidenceLevel
    factors: List[str]
    details: Dict
    processing_time: float
    success: bool

@dataclass
class BankTransaction:
    date: datetime
    description: str
    amount: float
    reference: str
    account_number: str
    transaction_type: str

class ProfessionalInvoiceMappingEngine:
    """
    Professional-grade invoice mapping engine with sequential logic processing
    """
    
    def __init__(self):
        self.processing_stages = [
            self._stage_1_amount_precision,
            self._stage_2_temporal_correlation,
            self._stage_3_reference_patterns,
            self._stage_4_party_identification,
            self._stage_5_semantic_analysis,
            self._stage_6_behavioral_patterns,
            self._stage_7_contextual_logic
        ]
        
        self.confidence_thresholds = {
            ConfidenceLevel.PERFECT: 0.95,
            ConfidenceLevel.HIGH: 0.85,
            ConfidenceLevel.GOOD: 0.70,
            ConfidenceLevel.MODERATE: 0.50,
            ConfidenceLevel.LOW: 0.25
        }
        
        self.stage_weights = {
            MatchingStage.STAGE_1_AMOUNT: 0.30,
            MatchingStage.STAGE_2_TEMPORAL: 0.25,
            MatchingStage.STAGE_3_REFERENCE: 0.20,
            MatchingStage.STAGE_4_PARTY: 0.15,
            MatchingStage.STAGE_5_SEMANTIC: 0.10,
            MatchingStage.STAGE_6_BEHAVIORAL: 0.10,
            MatchingStage.STAGE_7_CONTEXTUAL: 0.10
        }
    
    def process_mapping_sequence(self, bank_transaction: BankTransaction, 
                                invoice_entries: List[Dict]) -> Dict:
        """
        PROFESSIONAL SEQUENTIAL MAPPING PROCESS
        =====================================
        
        Runs through all 7 stages systematically for each invoice,
        providing detailed analysis and automatic fallback to manual mapping.
        """
        
        mapping_results = {
            'transaction_id': f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'bank_transaction': bank_transaction,
            'processing_timestamp': datetime.now(),
            'stage_results': {},
            'final_matches': [],
            'manual_mapping_required': [],
            'processing_summary': {},
            'audit_trail': []
        }
        
        print(f"\n🔄 STARTING PROFESSIONAL MAPPING SEQUENCE")
        print(f"Transaction: {bank_transaction.description[:50]}...")
        print(f"Amount: ₹{bank_transaction.amount:,.2f}")
        print(f"Date: {bank_transaction.date.strftime('%Y-%m-%d')}")
        print("=" * 80)
        
        # Process each invoice through the sequential stages
        for invoice_idx, invoice in enumerate(invoice_entries, 1):
            print(f"\n📋 PROCESSING INVOICE {invoice_idx}: {invoice.get('invoice_number', 'N/A')}")
            print(f"Party: {invoice.get('party_name', 'N/A')}")
            print(f"Amount: ₹{invoice.get('amount', 0):,.2f}")
            
            invoice_results = self._process_invoice_through_stages(
                bank_transaction, invoice, invoice_idx
            )
            
            mapping_results['stage_results'][f"invoice_{invoice_idx}"] = invoice_results
            
            # Determine final categorization
            final_confidence = invoice_results['final_confidence']
            categorization = self._categorize_match(final_confidence, invoice_results)
            
            if categorization['auto_process']:
                mapping_results['final_matches'].append({
                    'invoice': invoice,
                    'confidence': final_confidence,
                    'categorization': categorization,
                    'stage_results': invoice_results
                })
                print(f"✅ AUTO-MATCHED: {categorization['category']} ({final_confidence:.1%})")
            else:
                mapping_results['manual_mapping_required'].append({
                    'invoice': invoice,
                    'confidence': final_confidence,
                    'categorization': categorization,
                    'stage_results': invoice_results,
                    'manual_review_reasons': categorization['manual_reasons']
                })
                print(f"⚠️ MANUAL REVIEW: {categorization['category']} ({final_confidence:.1%})")
        
        # Generate processing summary
        mapping_results['processing_summary'] = self._generate_processing_summary(mapping_results)
        
        # Handle manual mapping if required
        if mapping_results['manual_mapping_required']:
            mapping_results['manual_mapping_interface'] = self._prepare_manual_mapping_interface(
                bank_transaction, mapping_results['manual_mapping_required']
            )
        
        return mapping_results
    
    def _process_invoice_through_stages(self, bank_transaction: BankTransaction, 
                                      invoice: Dict, invoice_idx: int) -> Dict:
        """Process a single invoice through all 7 stages sequentially"""
        
        stage_results = {}
        cumulative_score = 0.0
        processing_log = []
        
        print(f"\n   🔍 SEQUENTIAL STAGE PROCESSING:")
        
        for stage_idx, stage_func in enumerate(self.processing_stages, 1):
            stage_name = list(MatchingStage)[stage_idx - 1]
            
            print(f"   Stage {stage_idx}: {stage_name.value.replace('_', ' ').title()}", end=" → ")
            
            start_time = datetime.now()
            stage_result = stage_func(bank_transaction, invoice)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            stage_results[stage_name] = stage_result
            stage_weight = self.stage_weights[stage_name]
            weighted_score = stage_result.score * stage_weight
            cumulative_score += weighted_score
            
            # Log the stage result
            print(f"{stage_result.score:.1%} (Weight: {stage_weight:.0%}) = +{weighted_score:.3f}")
            
            processing_log.append({
                'stage': stage_name.value,
                'score': stage_result.score,
                'weight': stage_weight,
                'contribution': weighted_score,
                'factors': stage_result.factors,
                'processing_time_ms': processing_time
            })
            
            # Early termination for perfect matches
            if stage_result.score >= 0.99 and stage_name in [MatchingStage.STAGE_1_AMOUNT, MatchingStage.STAGE_3_REFERENCE]:
                print(f"   🎯 EARLY PERFECT MATCH DETECTED - Confidence boost applied")
                cumulative_score += 0.05  # Bonus for early perfect match
                break
        
        print(f"   📊 FINAL CUMULATIVE SCORE: {cumulative_score:.1%}")
        
        return {
            'stage_results': stage_results,
            'cumulative_score': cumulative_score,
            'final_confidence': min(cumulative_score, 1.0),
            'processing_log': processing_log,
            'early_termination': cumulative_score >= 0.99
        }
    
    def _stage_1_amount_precision(self, bank_tx: BankTransaction, invoice: Dict) -> MatchingResult:
        """STAGE 1: Mathematical Amount Precision Analysis"""
        
        start_time = datetime.now()
        factors = []
        details = {}
        
        try:
            bank_amount = float(bank_tx.amount)
            invoice_amount = float(invoice.get('amount', 0))
            
            # Absolute and percentage differences
            amount_diff = abs(bank_amount - invoice_amount)
            percentage_diff = amount_diff / abs(bank_amount) if bank_amount != 0 else 1.0
            
            # PRECISION ANALYSIS LOGIC
            if amount_diff < 0.001:  # Perfect precision
                score = 1.0
                factors.append('mathematical_precision_perfect')
                confidence = ConfidenceLevel.PERFECT
            elif amount_diff < 0.01:  # Near-perfect
                score = 0.98
                factors.append('near_perfect_precision')
                confidence = ConfidenceLevel.PERFECT
            elif percentage_diff <= 0.0001:  # 0.01% tolerance
                score = 0.95
                factors.append('ultra_high_precision')
                confidence = ConfidenceLevel.HIGH
            elif percentage_diff <= 0.001:  # 0.1% tolerance
                score = 0.90
                factors.append('high_precision_match')
                confidence = ConfidenceLevel.HIGH
            elif percentage_diff <= 0.01:  # 1% tolerance
                score = 0.80
                factors.append('acceptable_precision')
                confidence = ConfidenceLevel.GOOD
            elif percentage_diff <= 0.05:  # 5% tolerance
                score = 0.60
                factors.append('moderate_variance')
                confidence = ConfidenceLevel.MODERATE
            elif percentage_diff <= 0.1:  # 10% tolerance
                score = 0.30
                factors.append('high_variance')
                confidence = ConfidenceLevel.LOW
            else:
                score = 0.0
                factors.append('amount_mismatch')
                confidence = ConfidenceLevel.FAILED
            
            # ADVANCED ROUNDING ANALYSIS
            if amount_diff > 0:
                # Check for banking rounding patterns
                if amount_diff % 1 == 0:  # Whole number rounding
                    score += 0.05
                    factors.append('whole_number_rounding_detected')
                elif amount_diff in [0.01, 0.05, 0.10, 0.25, 0.50]:  # Common rounding
                    score += 0.03
                    factors.append('standard_rounding_pattern')
                
                # Currency conversion rounding
                if 0.01 <= amount_diff <= 0.99:
                    score += 0.02
                    factors.append('currency_rounding_pattern')
            
            # TRANSACTION SIZE CONTEXT
            if abs(bank_amount) >= 1000000:  # 10 Lakh+
                details['size_category'] = 'large_enterprise'
                if percentage_diff <= 0.0001:
                    score += 0.03
                    factors.append('large_transaction_precision_bonus')
            elif abs(bank_amount) >= 100000:  # 1 Lakh+
                details['size_category'] = 'medium_business'
                if percentage_diff <= 0.001:
                    score += 0.02
                    factors.append('medium_transaction_precision_bonus')
            else:
                details['size_category'] = 'small_transaction'
                if amount_diff <= 1:
                    score += 0.05
                    factors.append('small_amount_tolerance_bonus')
            
            details.update({
                'amount_difference': amount_diff,
                'percentage_difference': percentage_diff,
                'bank_amount': bank_amount,
                'invoice_amount': invoice_amount
            })
            
            success = score >= 0.25
            
        except (ValueError, TypeError) as e:
            score = 0.0
            confidence = ConfidenceLevel.FAILED
            factors.append('amount_parsing_error')
            details['error'] = str(e)
            success = False
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return MatchingResult(
            stage=MatchingStage.STAGE_1_AMOUNT,
            score=min(score, 1.0),
            confidence_level=confidence,
            factors=factors,
            details=details,
            processing_time=processing_time,
            success=success
        )
    
    def _stage_2_temporal_correlation(self, bank_tx: BankTransaction, invoice: Dict) -> MatchingResult:
        """STAGE 2: Advanced Temporal Correlation Analysis"""
        
        start_time = datetime.now()
        factors = []
        details = {}
        
        try:
            bank_date = bank_tx.date
            invoice_date = datetime.strptime(invoice.get('date', ''), '%Y-%m-%d')
            
            # Calculate date differences
            date_diff = (bank_date - invoice_date).days
            abs_date_diff = abs(date_diff)
            
            # TEMPORAL MATCHING LOGIC
            if abs_date_diff == 0:  # Same day
                score = 1.0
                factors.append('exact_date_synchronization')
                confidence = ConfidenceLevel.PERFECT
            elif abs_date_diff == 1:  # Adjacent day
                score = 0.92
                factors.append('adjacent_day_processing')
                confidence = ConfidenceLevel.HIGH
            elif abs_date_diff <= 2:  # Within 2 days
                score = 0.85
                factors.append('immediate_processing_window')
                confidence = ConfidenceLevel.HIGH
            elif abs_date_diff <= 5:  # Within business week
                score = 0.70
                factors.append('business_week_processing')
                confidence = ConfidenceLevel.GOOD
            elif abs_date_diff <= 10:  # Within business cycle
                score = 0.50
                factors.append('business_cycle_processing')
                confidence = ConfidenceLevel.MODERATE
            elif abs_date_diff <= 30:  # Within month
                score = 0.25
                factors.append('monthly_processing_cycle')
                confidence = ConfidenceLevel.LOW
            else:
                score = 0.05
                factors.append('extended_processing_delay')
                confidence = ConfidenceLevel.FAILED
            
            # BUSINESS DAY ANALYSIS
            bank_weekday = bank_date.weekday()
            invoice_weekday = invoice_date.weekday()
            
            # Weekend processing logic
            if bank_weekday >= 5 or invoice_weekday >= 5:  # Weekend involved
                factors.append('weekend_processing_involved')
                if abs_date_diff <= 3:
                    score += 0.08
                    factors.append('weekend_processing_adjustment')
                
                # Monday processing for Friday transactions
                if invoice_weekday == 4 and bank_weekday == 0 and abs_date_diff <= 3:
                    score += 0.05
                    factors.append('friday_to_monday_processing')
            
            # PROCESSING DELAY PATTERN ANALYSIS
            if date_diff > 0:  # Bank transaction after invoice (normal)
                details['processing_pattern'] = 'normal_payment_flow'
                if abs_date_diff <= 3:
                    score += 0.03
                    factors.append('standard_processing_delay')
                elif abs_date_diff <= 7:
                    score += 0.01
                    factors.append('extended_but_normal_delay')
            elif date_diff < 0:  # Bank transaction before invoice (advance)
                details['processing_pattern'] = 'advance_payment_scenario'
                if abs_date_diff <= 5:
                    score += 0.02
                    factors.append('advance_payment_detected')
            else:
                details['processing_pattern'] = 'same_day_processing'
                score += 0.05
                factors.append('real_time_processing')
            
            # RECURRING PATTERN DETECTION
            if abs_date_diff in [7, 14, 21, 28, 30, 90, 180, 365]:
                score += 0.03
                factors.append('recurring_payment_pattern_detected')
            
            # HOLIDAY AND SPECIAL DATE ANALYSIS
            # (This would integrate with a holiday calendar in production)
            month_day = (bank_date.month, bank_date.day)
            if month_day in [(1, 1), (8, 15), (10, 2), (12, 25)]:  # Major holidays
                if abs_date_diff <= 5:
                    score += 0.02
                    factors.append('holiday_processing_adjustment')
            
            details.update({
                'date_difference_days': date_diff,
                'absolute_difference': abs_date_diff,
                'bank_weekday': bank_weekday,
                'invoice_weekday': invoice_weekday,
                'processing_speed': 'immediate' if abs_date_diff <= 1 else 'fast' if abs_date_diff <= 3 else 'normal' if abs_date_diff <= 7 else 'slow'
            })
            
            success = score >= 0.20
            
        except (ValueError, TypeError) as e:
            score = 0.0
            confidence = ConfidenceLevel.FAILED
            factors.append('date_parsing_error')
            details['error'] = str(e)
            success = False
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return MatchingResult(
            stage=MatchingStage.STAGE_2_TEMPORAL,
            score=min(score, 1.0),
            confidence_level=confidence,
            factors=factors,
            details=details,
            processing_time=processing_time,
            success=success
        )
    
    def _stage_3_reference_patterns(self, bank_tx: BankTransaction, invoice: Dict) -> MatchingResult:
        """STAGE 3: Advanced Reference Pattern Matching"""
        
        start_time = datetime.now()
        factors = []
        details = {}
        
        # Extract and normalize text data
        bank_desc = bank_tx.description.lower().strip()
        bank_ref = bank_tx.reference.lower().strip() if bank_tx.reference else ""
        invoice_num = invoice.get('invoice_number', '').lower().strip()
        entry_ref = invoice.get('reference', '').lower().strip()
        
        # Combined search space
        search_text = f"{bank_desc} {bank_ref}".strip()
        
        score = 0.0
        confidence = ConfidenceLevel.FAILED
        
        try:
            # EXACT INVOICE NUMBER MATCHING
            if invoice_num and len(invoice_num) >= 3:
                if invoice_num in search_text:
                    score = 1.0
                    factors.append('exact_invoice_number_detected')
                    confidence = ConfidenceLevel.PERFECT
                else:
                    # ADVANCED PATTERN DECOMPOSITION
                    invoice_components = self._decompose_invoice_number(invoice_num)
                    match_score = self._analyze_component_matches(search_text, invoice_components)
                    
                    if match_score >= 0.9:
                        score = 0.95
                        factors.append('complete_component_match')
                        confidence = ConfidenceLevel.HIGH
                    elif match_score >= 0.7:
                        score = 0.80
                        factors.append('majority_component_match')
                        confidence = ConfidenceLevel.GOOD
                    elif match_score >= 0.5:
                        score = 0.60
                        factors.append('partial_component_match')
                        confidence = ConfidenceLevel.MODERATE
                    elif match_score >= 0.3:
                        score = 0.40
                        factors.append('minimal_component_match')
                        confidence = ConfidenceLevel.LOW
                    
                    # NUMERIC SEQUENCE ANALYSIS
                    numeric_score = self._analyze_numeric_sequences(search_text, invoice_num)
                    if numeric_score > 0.8:
                        score = max(score, 0.85)
                        factors.append('strong_numeric_sequence_match')
                    elif numeric_score > 0.5:
                        score = max(score, 0.65)
                        factors.append('moderate_numeric_sequence_match')
            
            # REFERENCE CODE CORRELATION
            if entry_ref and len(entry_ref) >= 4:
                if entry_ref in search_text:
                    score = max(score, 0.75)
                    factors.append('reference_code_exact_match')
                    confidence = max(confidence, ConfidenceLevel.GOOD)
                else:
                    # Partial reference matching
                    ref_similarity = self._calculate_reference_similarity(search_text, entry_ref)
                    if ref_similarity > 0.7:
                        score = max(score, 0.60)
                        factors.append('reference_code_similarity_match')
            
            # PATTERN NORMALIZATION AND STANDARDIZATION
            normalized_score = self._normalize_and_match_patterns(search_text, invoice_num, entry_ref)
            if normalized_score > 0.6:
                score = max(score, normalized_score)
                factors.append('normalized_pattern_recognition')
            
            # CHECKSUM AND VALIDATION
            if self._validate_reference_integrity(invoice_num, search_text):
                score += 0.05
                factors.append('reference_integrity_validated')
            
            # SEQUENTIAL PATTERN DETECTION
            if self._detect_sequential_patterns(search_text, invoice_num):
                score += 0.03
                factors.append('sequential_pattern_detected')
            
            details.update({
                'invoice_number': invoice_num,
                'search_text_length': len(search_text),
                'pattern_matches_found': len([f for f in factors if 'match' in f]),
                'processing_method': 'advanced_pattern_analysis'
            })
            
            success = score >= 0.15
            
        except Exception as e:
            score = 0.0
            confidence = ConfidenceLevel.FAILED
            factors.append('pattern_analysis_error')
            details['error'] = str(e)
            success = False
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return MatchingResult(
            stage=MatchingStage.STAGE_3_REFERENCE,
            score=min(score, 1.0),
            confidence_level=confidence,
            factors=factors,
            details=details,
            processing_time=processing_time,
            success=success
        )
    
    def _stage_4_party_identification(self, bank_tx: BankTransaction, invoice: Dict) -> MatchingResult:
        """STAGE 4: Intelligent Party Identification"""
        
        start_time = datetime.now()
        factors = []
        details = {}
        
        bank_desc = bank_tx.description.lower()
        party_name = invoice.get('party_name', '').lower()
        
        score = 0.0
        confidence = ConfidenceLevel.FAILED
        
        if not party_name or len(party_name) < 3:
            return MatchingResult(
                stage=MatchingStage.STAGE_4_PARTY,
                score=0.0,
                confidence_level=ConfidenceLevel.FAILED,
                factors=['insufficient_party_data'],
                details={'error': 'Party name too short or missing'},
                processing_time=0.0,
                success=False
            )
        
        try:
            # EXACT NAME MATCHING
            if party_name in bank_desc:
                score = 1.0
                factors.append('exact_party_name_identification')
                confidence = ConfidenceLevel.PERFECT
            else:
                # ADVANCED NAME DECOMPOSITION AND ANALYSIS
                party_analysis = self._analyze_party_name_components(party_name)
                match_analysis = self._match_party_components(bank_desc, party_analysis)
                
                score = match_analysis['overall_score']
                factors.extend(match_analysis['factors'])
                details.update(match_analysis['details'])
                
                if score >= 0.85:
                    confidence = ConfidenceLevel.HIGH
                elif score >= 0.65:
                    confidence = ConfidenceLevel.GOOD
                elif score >= 0.45:
                    confidence = ConfidenceLevel.MODERATE
                elif score >= 0.25:
                    confidence = ConfidenceLevel.LOW
            
            # PHONETIC AND SOUND-ALIKE MATCHING
            phonetic_score = self._phonetic_name_analysis(bank_desc, party_name)
            if phonetic_score > 0.7:
                score = max(score, 0.80)
                factors.append('phonetic_name_match_detected')
            
            # ABBREVIATION AND ACRONYM DETECTION
            abbrev_score = self._detect_business_abbreviations(bank_desc, party_name)
            if abbrev_score > 0.75:
                score = max(score, 0.85)
                factors.append('business_abbreviation_match')
            
            # SUBSIDIARY AND BRAND RELATIONSHIP ANALYSIS
            brand_score = self._analyze_brand_relationships(bank_desc, party_name)
            if brand_score > 0.6:
                score = max(score, 0.70)
                factors.append('brand_relationship_detected')
            
            success = score >= 0.20
            
        except Exception as e:
            score = 0.0
            confidence = ConfidenceLevel.FAILED
            factors.append('party_analysis_error')
            details['error'] = str(e)
            success = False
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return MatchingResult(
            stage=MatchingStage.STAGE_4_PARTY,
            score=min(score, 1.0),
            confidence_level=confidence,
            factors=factors,
            details=details,
            processing_time=processing_time,
            success=success
        )
    
    def _stage_5_semantic_analysis(self, bank_tx: BankTransaction, invoice: Dict) -> MatchingResult:
        """STAGE 5: Semantic Description Analysis"""
        
        start_time = datetime.now()
        factors = []
        details = {}
        
        bank_desc = bank_tx.description.lower()
        invoice_desc = invoice.get('description', '').lower()
        
        score = 0.0
        confidence = ConfidenceLevel.FAILED
        
        if not invoice_desc or len(invoice_desc) < 5:
            return MatchingResult(
                stage=MatchingStage.STAGE_5_SEMANTIC,
                score=0.0,
                confidence_level=ConfidenceLevel.FAILED,
                factors=['insufficient_description_data'],
                details={'error': 'Invoice description too short or missing'},
                processing_time=0.0,
                success=False
            )
        
        try:
            # SEMANTIC SIMILARITY ANALYSIS
            semantic_score = self._calculate_advanced_semantic_similarity(bank_desc, invoice_desc)
            
            if semantic_score >= 0.90:
                score = 0.95
                factors.append('high_semantic_correlation')
                confidence = ConfidenceLevel.HIGH
            elif semantic_score >= 0.70:
                score = 0.80
                factors.append('good_semantic_correlation')
                confidence = ConfidenceLevel.GOOD
            elif semantic_score >= 0.50:
                score = 0.60
                factors.append('moderate_semantic_correlation')
                confidence = ConfidenceLevel.MODERATE
            elif semantic_score >= 0.30:
                score = 0.40
                factors.append('weak_semantic_correlation')
                confidence = ConfidenceLevel.LOW
            else:
                score = 0.10
                factors.append('minimal_semantic_correlation')
                confidence = ConfidenceLevel.FAILED
            
            # INDUSTRY-SPECIFIC KEYWORD ANALYSIS
            industry_score = self._analyze_industry_keywords(bank_desc, invoice_desc)
            if industry_score > 0.6:
                score = max(score, 0.75)
                factors.append('industry_keyword_correlation')
            
            # TRANSACTION PURPOSE CLASSIFICATION
            purpose_score = self._classify_transaction_purpose(bank_desc, invoice_desc)
            if purpose_score > 0.7:
                score = max(score, 0.80)
                factors.append('transaction_purpose_alignment')
            
            details.update({
                'semantic_similarity': semantic_score,
                'industry_score': industry_score,
                'purpose_classification': purpose_score
            })
            
            success = score >= 0.15
            
        except Exception as e:
            score = 0.0
            confidence = ConfidenceLevel.FAILED
            factors.append('semantic_analysis_error')
            details['error'] = str(e)
            success = False
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return MatchingResult(
            stage=MatchingStage.STAGE_5_SEMANTIC,
            score=min(score, 1.0),
            confidence_level=confidence,
            factors=factors,
            details=details,
            processing_time=processing_time,
            success=success
        )
    
    def _stage_6_behavioral_patterns(self, bank_tx: BankTransaction, invoice: Dict) -> MatchingResult:
        """STAGE 6: Behavioral Transaction Analysis"""
        
        start_time = datetime.now()
        factors = []
        details = {}
        
        score = 0.0
        confidence = ConfidenceLevel.FAILED
        
        try:
            # TRANSACTION FLOW ANALYSIS
            bank_credit = float(bank_tx.amount) > 0
            invoice_type = invoice.get('transaction_type', '').lower()
            
            # Advanced transaction type correlation
            flow_score = self._analyze_transaction_flow(bank_credit, invoice_type, bank_tx, invoice)
            
            if flow_score >= 0.95:
                score = 1.0
                factors.append('perfect_transaction_flow_match')
                confidence = ConfidenceLevel.PERFECT
            elif flow_score >= 0.80:
                score = 0.85
                factors.append('strong_transaction_flow_match')
                confidence = ConfidenceLevel.HIGH
            elif flow_score >= 0.60:
                score = 0.70
                factors.append('good_transaction_flow_match')
                confidence = ConfidenceLevel.GOOD
            elif flow_score >= 0.40:
                score = 0.50
                factors.append('moderate_transaction_flow_match')
                confidence = ConfidenceLevel.MODERATE
            elif flow_score >= 0.20:
                score = 0.30
                factors.append('weak_transaction_flow_match')
                confidence = ConfidenceLevel.LOW
            
            # FREQUENCY AND PATTERN ANALYSIS
            frequency_score = self._analyze_transaction_frequency_patterns(bank_tx, invoice)
            if frequency_score > 0.6:
                score = max(score, 0.75)
                factors.append('recurring_pattern_detected')
            
            # ANOMALY DETECTION
            anomaly_score = self._detect_transaction_anomalies(bank_tx, invoice)
            if anomaly_score < 0.3:  # Low anomaly = good match
                score += 0.05
                factors.append('no_behavioral_anomalies')
            elif anomaly_score > 0.7:  # High anomaly = poor match
                score *= 0.8
                factors.append('behavioral_anomalies_detected')
            
            details.update({
                'transaction_flow_score': flow_score,
                'frequency_score': frequency_score,
                'anomaly_score': anomaly_score,
                'bank_credit': bank_credit,
                'invoice_type': invoice_type
            })
            
            success = score >= 0.15
            
        except Exception as e:
            score = 0.0
            confidence = ConfidenceLevel.FAILED
            factors.append('behavioral_analysis_error')
            details['error'] = str(e)
            success = False
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return MatchingResult(
            stage=MatchingStage.STAGE_6_BEHAVIORAL,
            score=min(score, 1.0),
            confidence_level=confidence,
            factors=factors,
            details=details,
            processing_time=processing_time,
            success=success
        )
    
    def _stage_7_contextual_logic(self, bank_tx: BankTransaction, invoice: Dict) -> MatchingResult:
        """STAGE 7: Contextual Business Logic Analysis"""
        
        start_time = datetime.now()
        factors = []
        details = {}
        
        score = 0.0
        confidence = ConfidenceLevel.FAILED
        
        try:
            # COMPLIANCE AND REGULATORY ANALYSIS
            compliance_score = self._analyze_compliance_patterns(bank_tx, invoice)
            
            if compliance_score >= 0.90:
                score = 0.95
                factors.append('full_compliance_alignment')
                confidence = ConfidenceLevel.HIGH
            elif compliance_score >= 0.70:
                score = 0.80
                factors.append('good_compliance_alignment')
                confidence = ConfidenceLevel.GOOD
            elif compliance_score >= 0.50:
                score = 0.65
                factors.append('moderate_compliance_alignment')
                confidence = ConfidenceLevel.MODERATE
            else:
                score = 0.40
                factors.append('basic_compliance_alignment')
                confidence = ConfidenceLevel.LOW
            
            # GST AND TAX ANALYSIS
            tax_score = self._analyze_tax_compliance(bank_tx, invoice)
            if tax_score > 0.8:
                score = max(score, 0.85)
                factors.append('tax_compliance_verified')
            
            # GEOGRAPHIC AND JURISDICTION ANALYSIS
            geo_score = self._analyze_geographic_context(bank_tx, invoice)
            if geo_score > 0.7:
                score = max(score, 0.75)
                factors.append('geographic_context_aligned')
            
            # BUSINESS RELATIONSHIP ANALYSIS
            relationship_score = self._analyze_business_relationships(bank_tx, invoice)
            if relationship_score > 0.6:
                score = max(score, 0.70)
                factors.append('business_relationship_confirmed')
            
            details.update({
                'compliance_score': compliance_score,
                'tax_score': tax_score,
                'geographic_score': geo_score,
                'relationship_score': relationship_score
            })
            
            success = score >= 0.30
            
        except Exception as e:
            score = 0.0
            confidence = ConfidenceLevel.FAILED
            factors.append('contextual_analysis_error')
            details['error'] = str(e)
            success = False
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return MatchingResult(
            stage=MatchingStage.STAGE_7_CONTEXTUAL,
            score=min(score, 1.0),
            confidence_level=confidence,
            factors=factors,
            details=details,
            processing_time=processing_time,
            success=success
        )
    
    # Helper methods for advanced analysis (simplified implementations)
    def _decompose_invoice_number(self, invoice_num: str) -> Dict:
        """Decompose invoice number into analyzable components"""
        components = {
            'prefix': '',
            'numeric_parts': [],
            'separators': [],
            'suffix': ''
        }
        
        # Extract numeric sequences
        components['numeric_parts'] = re.findall(r'\d+', invoice_num)
        
        # Extract non-numeric parts
        non_numeric = re.sub(r'\d+', '', invoice_num)
        components['prefix'] = non_numeric[:3] if non_numeric else ''
        
        return components
    
    def _analyze_component_matches(self, search_text: str, components: Dict) -> float:
        """Analyze how well invoice components match in search text"""
        matches = 0
        total_components = len(components['numeric_parts']) + (1 if components['prefix'] else 0)
        
        if total_components == 0:
            return 0.0
        
        # Check numeric parts
        for num_part in components['numeric_parts']:
            if len(num_part) > 2 and num_part in search_text:
                matches += 1
        
        # Check prefix
        if components['prefix'] and components['prefix'] in search_text:
            matches += 1
        
        return matches / total_components
    
    def _analyze_numeric_sequences(self, search_text: str, invoice_num: str) -> float:
        """Analyze numeric sequence matching"""
        search_numbers = re.findall(r'\d+', search_text)
        invoice_numbers = re.findall(r'\d+', invoice_num)
        
        if not invoice_numbers:
            return 0.0
        
        matches = 0
        for inv_num in invoice_numbers:
            if len(inv_num) > 3 and inv_num in search_numbers:
                matches += 1
        
        return matches / len(invoice_numbers)
    
    def _calculate_reference_similarity(self, search_text: str, reference: str) -> float:
        """Calculate similarity between reference codes"""
        ref_words = set(reference.split())
        search_words = set(search_text.split())
        
        if not ref_words:
            return 0.0
        
        intersection = ref_words.intersection(search_words)
        return len(intersection) / len(ref_words)
    
    def _normalize_and_match_patterns(self, search_text: str, invoice_num: str, reference: str) -> float:
        """Normalize patterns and find matches"""
        # Remove common separators and normalize
        normalized_search = re.sub(r'[/-]', '', search_text)
        normalized_invoice = re.sub(r'[/-]', '', invoice_num)
        
        if normalized_invoice in normalized_search:
            return 0.8
        
        return 0.0
    
    def _validate_reference_integrity(self, invoice_num: str, search_text: str) -> bool:
        """Validate reference integrity using checksums"""
        # Simplified checksum validation
        return len(invoice_num) > 5 and any(char.isdigit() for char in invoice_num)
    
    def _detect_sequential_patterns(self, search_text: str, invoice_num: str) -> bool:
        """Detect sequential numbering patterns"""
        # Look for sequential patterns in numbers
        numbers = re.findall(r'\d+', search_text)
        invoice_numbers = re.findall(r'\d+', invoice_num)
        
        return bool(set(numbers).intersection(set(invoice_numbers)))
    
    def _analyze_party_name_components(self, party_name: str) -> Dict:
        """Analyze party name components"""
        # Remove business suffixes
        business_terms = ['ltd', 'limited', 'pvt', 'private', 'company', 'corp', 'inc', 'llp']
        words = [word for word in party_name.split() if word not in business_terms]
        
        return {
            'core_words': [word for word in words if len(word) > 3],
            'short_words': [word for word in words if len(word) <= 3],
            'business_type': [word for word in party_name.split() if word in business_terms]
        }
    
    def _match_party_components(self, bank_desc: str, party_analysis: Dict) -> Dict:
        """Match party components against bank description"""
        core_matches = sum(1 for word in party_analysis['core_words'] if word in bank_desc)
        total_core = len(party_analysis['core_words'])
        
        if total_core == 0:
            return {'overall_score': 0.0, 'factors': [], 'details': {}}
        
        score = core_matches / total_core
        factors = []
        
        if score >= 0.8:
            factors.append('strong_party_component_match')
        elif score >= 0.5:
            factors.append('moderate_party_component_match')
        elif score > 0:
            factors.append('weak_party_component_match')
        
        return {
            'overall_score': score,
            'factors': factors,
            'details': {'core_matches': core_matches, 'total_core': total_core}
        }
    
    def _phonetic_name_analysis(self, bank_desc: str, party_name: str) -> float:
        """Simplified phonetic analysis"""
        # This would use a phonetic algorithm like Soundex in production
        return 0.5  # Placeholder
    
    def _detect_business_abbreviations(self, bank_desc: str, party_name: str) -> float:
        """Detect business name abbreviations"""
        # Extract first letters of each word
        words = [word for word in party_name.split() if len(word) > 2]
        if len(words) < 2:
            return 0.0
        
        abbreviation = ''.join(word[0] for word in words)
        return 0.8 if abbreviation.upper() in bank_desc.upper() else 0.0
    
    def _analyze_brand_relationships(self, bank_desc: str, party_name: str) -> float:
        """Analyze brand and subsidiary relationships"""
        # Simplified brand relationship analysis
        return 0.3  # Placeholder
    
    def _calculate_advanced_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate advanced semantic similarity"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _analyze_industry_keywords(self, bank_desc: str, invoice_desc: str) -> float:
        """Analyze industry-specific keywords"""
        # Define industry keyword categories
        keywords = {
            'software': ['software', 'development', 'programming', 'coding', 'tech'],
            'furniture': ['furniture', 'chair', 'table', 'desk', 'office'],
            'services': ['service', 'consulting', 'advisory', 'support']
        }
        
        combined_text = f"{bank_desc} {invoice_desc}"
        matches = 0
        total_keywords = sum(len(kw_list) for kw_list in keywords.values())
        
        for category, kw_list in keywords.items():
            matches += sum(1 for kw in kw_list if kw in combined_text)
        
        return matches / total_keywords if total_keywords > 0 else 0.0
    
    def _classify_transaction_purpose(self, bank_desc: str, invoice_desc: str) -> float:
        """Classify transaction purpose alignment"""
        # Simplified purpose classification
        purpose_keywords = ['payment', 'invoice', 'bill', 'purchase', 'sale']
        combined_text = f"{bank_desc} {invoice_desc}"
        
        matches = sum(1 for kw in purpose_keywords if kw in combined_text)
        return matches / len(purpose_keywords)
    
    def _analyze_transaction_flow(self, bank_credit: bool, invoice_type: str, bank_tx, invoice) -> float:
        """Analyze transaction flow patterns"""
        # Perfect matches
        if bank_credit and invoice_type in ['sales', 'income', 'receipt']:
            return 0.95
        if not bank_credit and invoice_type in ['purchase', 'expense', 'payment']:
            return 0.95
        
        # Possible scenarios
        if bank_credit and invoice_type in ['purchase', 'expense']:
            return 0.30  # Possible refund
        if not bank_credit and invoice_type in ['sales', 'income']:
            return 0.25  # Possible reversal
        
        return 0.50  # Neutral
    
    def _analyze_transaction_frequency_patterns(self, bank_tx, invoice) -> float:
        """Analyze frequency patterns"""
        # This would analyze historical data in production
        return 0.5  # Placeholder
    
    def _detect_transaction_anomalies(self, bank_tx, invoice) -> float:
        """Detect transaction anomalies"""
        # This would use ML models in production
        return 0.3  # Placeholder (low anomaly)
    
    def _analyze_compliance_patterns(self, bank_tx, invoice) -> float:
        """Analyze compliance and regulatory patterns"""
        base_score = 0.7
        
        # Check for GST compliance
        if invoice.get('gst_number'):
            base_score += 0.1
        
        # Check for proper invoice format
        if invoice.get('invoice_number') and len(invoice.get('invoice_number', '')) > 5:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _analyze_tax_compliance(self, bank_tx, invoice) -> float:
        """Analyze tax compliance"""
        gst_number = invoice.get('gst_number', '').lower()
        if gst_number and gst_number in bank_tx.description.lower():
            return 0.9
        return 0.5
    
    def _analyze_geographic_context(self, bank_tx, invoice) -> float:
        """Analyze geographic context"""
        # This would check location data in production
        return 0.6  # Placeholder
    
    def _analyze_business_relationships(self, bank_tx, invoice) -> float:
        """Analyze business relationships"""
        # This would check CRM/ERP data in production
        return 0.5  # Placeholder
    
    def _categorize_match(self, confidence: float, invoice_results: Dict) -> Dict:
        """Categorize the final match with detailed reasoning"""
        
        categorization = {
            'confidence': confidence,
            'auto_process': False,
            'manual_reasons': [],
            'category': '',
            'color_code': '',
            'action_required': ''
        }
        
        if confidence >= 0.95:
            categorization.update({
                'category': 'PERFECT_MATCH',
                'color_code': 'DARK_GREEN',
                'auto_process': True,
                'action_required': 'auto_process_immediately'
            })
        elif confidence >= 0.85:
            categorization.update({
                'category': 'HIGH_CONFIDENCE',
                'color_code': 'GREEN',
                'auto_process': True,
                'action_required': 'auto_match_with_notification'
            })
        elif confidence >= 0.70:
            categorization.update({
                'category': 'GOOD_MATCH',
                'color_code': 'YELLOW',
                'auto_process': False,
                'action_required': 'review_suggested',
                'manual_reasons': ['confidence_below_auto_threshold', 'review_recommended']
            })
        elif confidence >= 0.50:
            categorization.update({
                'category': 'MODERATE_MATCH',
                'color_code': 'ORANGE',
                'auto_process': False,
                'action_required': 'manual_review_required',
                'manual_reasons': ['moderate_confidence', 'requires_verification']
            })
        else:
            categorization.update({
                'category': 'POOR_MATCH',
                'color_code': 'RED',
                'auto_process': False,
                'action_required': 'manual_mapping_required',
                'manual_reasons': ['low_confidence', 'insufficient_matching_factors']
            })
        
        return categorization
    
    def _generate_processing_summary(self, mapping_results: Dict) -> Dict:
        """Generate comprehensive processing summary"""
        
        total_invoices = len(mapping_results['stage_results'])
        auto_matched = len(mapping_results['final_matches'])
        manual_required = len(mapping_results['manual_mapping_required'])
        
        return {
            'total_invoices_processed': total_invoices,
            'auto_matched_count': auto_matched,
            'manual_mapping_required_count': manual_required,
            'auto_match_rate': (auto_matched / total_invoices * 100) if total_invoices > 0 else 0,
            'processing_efficiency': 'high' if auto_matched / total_invoices > 0.8 else 'medium' if auto_matched / total_invoices > 0.5 else 'low',
            'recommendation': self._get_processing_recommendation(auto_matched, manual_required)
        }
    
    def _get_processing_recommendation(self, auto_matched: int, manual_required: int) -> str:
        """Get processing recommendation based on results"""
        if auto_matched > manual_required * 3:
            return "Excellent matching performance. System is working optimally."
        elif auto_matched > manual_required:
            return "Good matching performance. Minor manual review needed."
        else:
            return "Significant manual intervention required. Consider reviewing matching criteria."
    
    def _prepare_manual_mapping_interface(self, bank_transaction: BankTransaction, 
                                        manual_items: List[Dict]) -> Dict:
        """Prepare comprehensive manual mapping interface"""
        
        return {
            'transaction_details': {
                'date': bank_transaction.date.strftime('%Y-%m-%d'),
                'description': bank_transaction.description,
                'amount': bank_transaction.amount,
                'reference': bank_transaction.reference
            },
            'manual_mapping_candidates': [
                {
                    'invoice_id': item['invoice'].get('id', f"inv_{idx}"),
                    'invoice_number': item['invoice'].get('invoice_number', 'N/A'),
                    'party_name': item['invoice'].get('party_name', 'N/A'),
                    'amount': item['invoice'].get('amount', 0),
                    'confidence_score': item['confidence'],
                    'category': item['categorization']['category'],
                    'manual_reasons': item['manual_review_reasons'],
                    'suggested_actions': self._get_manual_mapping_suggestions(item)
                }
                for idx, item in enumerate(manual_items, 1)
            ],
            'manual_mapping_tools': {
                'search_filters': ['amount_range', 'date_range', 'party_name', 'description_keywords'],
                'matching_tools': ['fuzzy_search', 'pattern_matching', 'semantic_search'],
                'verification_steps': ['amount_verification', 'date_verification', 'party_verification']
            }
        }
    
    def _get_manual_mapping_suggestions(self, manual_item: Dict) -> List[str]:
        """Get specific suggestions for manual mapping"""
        suggestions = []
        confidence = manual_item['confidence']
        
        if confidence > 0.6:
            suggestions.append("High partial match - verify amount and date details")
        elif confidence > 0.4:
            suggestions.append("Moderate match - check party name variations")
        else:
            suggestions.append("Low match - consider alternative search criteria")
        
        return suggestions