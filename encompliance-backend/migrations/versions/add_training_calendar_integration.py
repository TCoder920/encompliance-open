"""
Description: Add training calendar integration foreign keys to calendar_events table
Purpose: Enables linking calendar events to training programs, assignments, and completions
Educational Note: Alembic migration pattern for schema updates
Reference: Alembic documentation on migration scripts
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'train_cal_int_01'
down_revision = 'task_management_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add training integration fields to calendar_events table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()
    
    if 'calendar_events' in table_names:
        columns = [c['name'] for c in inspector.get_columns('calendar_events')]
        existing_indexes = [i['name'] for i in inspector.get_indexes('calendar_events')]
        
        # Add training_program_id
        if 'training_program_id' not in columns:
            op.add_column('calendar_events', sa.Column('training_program_id', sa.Integer(), nullable=True))
            # Create index only if newly added or missing (check name)
            if 'idx_calendar_events_training_program_id' not in existing_indexes:
                 op.create_index('idx_calendar_events_training_program_id', 'calendar_events', ['training_program_id'])
            # Create FK
            op.create_foreign_key(
                'fk_calendar_events_training_program_id',
                'calendar_events', 'training_programs',
                ['training_program_id'], ['id'],
                ondelete='CASCADE'
            )

        # Add training_assignment_id
        if 'training_assignment_id' not in columns:
            op.add_column('calendar_events', sa.Column('training_assignment_id', sa.Integer(), nullable=True))
            if 'idx_calendar_events_training_assignment_id' not in existing_indexes:
                 op.create_index('idx_calendar_events_training_assignment_id', 'calendar_events', ['training_assignment_id'])
            op.create_foreign_key(
                'fk_calendar_events_training_assignment_id',
                'calendar_events', 'training_assignments',
                ['training_assignment_id'], ['id'],
                ondelete='CASCADE'
            )

        # Add training_completion_id
        if 'training_completion_id' not in columns:
            op.add_column('calendar_events', sa.Column('training_completion_id', sa.Integer(), nullable=True))
            if 'idx_calendar_events_training_completion_id' not in existing_indexes:
                 op.create_index('idx_calendar_events_training_completion_id', 'calendar_events', ['training_completion_id'])
            op.create_foreign_key(
                'fk_calendar_events_training_completion_id',
                'calendar_events', 'training_completions',
                ['training_completion_id'], ['id'],
                ondelete='CASCADE'
            )

def downgrade() -> None:
    """Remove training integration fields from calendar_events table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()
    
    if 'calendar_events' in table_names:
        columns = [c['name'] for c in inspector.get_columns('calendar_events')]
        existing_indexes = [i['name'] for i in inspector.get_indexes('calendar_events')]
        
        # Drop training_completion_id
        if 'idx_calendar_events_training_completion_id' in existing_indexes:
            op.drop_index('idx_calendar_events_training_completion_id', table_name='calendar_events')
        op.drop_constraint('fk_calendar_events_training_completion_id', 'calendar_events', type_='foreignkey')
        if 'training_completion_id' in columns:
            op.drop_column('calendar_events', 'training_completion_id')

        # Drop training_assignment_id
        if 'idx_calendar_events_training_assignment_id' in existing_indexes:
             op.drop_index('idx_calendar_events_training_assignment_id', table_name='calendar_events')
        op.drop_constraint('fk_calendar_events_training_assignment_id', 'calendar_events', type_='foreignkey')
        if 'training_assignment_id' in columns:
            op.drop_column('calendar_events', 'training_assignment_id')
            
        # Drop training_program_id
        if 'idx_calendar_events_training_program_id' in existing_indexes:
             op.drop_index('idx_calendar_events_training_program_id', table_name='calendar_events')
        op.drop_constraint('fk_calendar_events_training_program_id', 'calendar_events', type_='foreignkey')
        if 'training_program_id' in columns:
            op.drop_column('calendar_events', 'training_program_id') 