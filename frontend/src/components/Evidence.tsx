import type { Assessment } from '@/types'
import { Badge } from './ui/primitives'

export function Evidence({ assessment }: { assessment: Assessment }) {
  return <details className="evidence"><summary>Assessment evidence</summary>
    <Badge tone="cyan">{assessment.assessment_kind.replaceAll('_', ' ')}</Badge>
    <dl>
      <dt>Source</dt><dd>{assessment.source ?? 'Not supplied'}</dd>
      <dt>Provenance</dt><dd>{assessment.provenance}</dd>
      <dt>Evidence reference</dt><dd>{assessment.evidence_ref ?? 'Not supplied for base assertion'}</dd>
      <dt>Authored record date</dt><dd>{assessment.recorded_value ?? 'Unknown'} · precision: {assessment.recorded_precision}</dd>
      <dt>Supplied author label</dt><dd>{assessment.supplied_author_label ?? 'Not supplied'}</dd>
      <dt>Human physical review</dt><dd>{assessment.human_reviewed ? assessment.human_reviewer : 'No technician review recorded'}</dd>
      <dt>Imported at (server UTC)</dt><dd>{assessment.imported_at}</dd>
      <dt>Imported by</dt><dd>{assessment.imported_by}</dd>
      <dt>Scope</dt><dd>{assessment.acceptance_scope}</dd>
    </dl><p className="caption">{assessment.context_source}. Import time is separate from the authored record date.</p>
  </details>
}
