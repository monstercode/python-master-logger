from master_logger.master_logger import Logger
# This code shows how trying to instantiate the class doesn't overwrite the singleton instance attributes.
# In python if __new__ returns a new object, it calls __init__ on that object.
# When calling the __new__ method (by using Logger(args..)) it calls __new__, which returns the singleton instance
# and Python automatically calls __init__ on that object. We don't want to do that because we don't want to
# to empty attributes already set to the singleton instance

first_logger = Logger(log_line_number=True)
second_logger = Logger(log_line_number=False)

print(f"first logger and second logger point to the same object? {first_logger is second_logger}\n")
print(f"firt_logger is initialized with log_line_number=True. first_logger.log_line_number: {first_logger.log_line_number}\n")
print(f"second_logger doesn't override the initialized parameter. Second logger sets log_line_number=False but it should not change it as it's already initialized. second_logger.log_line_number: {first_logger.log_line_number} -> should be still True from first_logger")