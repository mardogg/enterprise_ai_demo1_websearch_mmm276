export type TroubleshootResult = {
  productType: string;
  brand: string;
  model: string;
  issueSummary: string;
  observations: string[];
  hypothesis: string;
  probableCauses?: string[];
  actionPlan: string[];
  escalationCriteria: string[];
  warnings?: string[];
  suggestedKeywords: string[];
};

export async function generatePlan(
  productType: string,
  brand: string,
  model: string,
  issue: string,
  details?: string
): Promise<TroubleshootResult> {
  try {
    const response = await fetch('/api/generate-plan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        productType,
        brand,
        model,
        issue,
        details: details || '',
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to generate plan');
    }

    const data = await response.json();
    
    return {
      productType,
      brand,
      model,
      issueSummary: issue,
      observations: data.observations || [],
      hypothesis: data.hypothesis || 'No hypothesis generated',
      probableCauses: data.probableCauses,
      actionPlan: data.actionPlan || [],
      escalationCriteria: data.escalationCriteria || [],
      warnings: data.warnings,
      suggestedKeywords: data.suggestedKeywords || [],
    };
  } catch (error) {
    console.error('Error generating plan:', error);
    throw error;
  }
}
