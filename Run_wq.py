import Utils
import Work_queue_manager as wqm
import Subject_Management as sm

if __name__ == "__main__":
    # Load subjects file
    sdf = sm.load_subjects()

    # Run work queue
    Utils.log('Checking work queue')
    wqm.run_wq()
